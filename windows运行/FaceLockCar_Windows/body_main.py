"""Windows CPU port of the body tracking pipeline.

The Orange Pi NPU backend remains available with ``--person-backend npu`` on
the board; Windows uses the OpenCV NanoDet CPU backend by default.
"""
import argparse
from collections import deque
import json
import signal
import sys
import time
from pathlib import Path
import cv2
import numpy as np
from main import LatestCamera, Output
from core import Snapshot, control_fields
from steering import Steering
from inference_worker import PersonWorker
from body_identity import BodyIdentities, BodySelection
from single_person import SinglePersonPolicy
from body_hud import BodyHUD
from performance import PerformanceMeter

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--camera',type=int,default=0)
    p.add_argument('--camera-backend',choices=('auto','dshow','msmf'),default='dshow' if sys.platform=='win32' else 'auto',
                   help='Windows camera API; try msmf if DirectShow cannot read frames')
    p.add_argument('--width',type=int,default=640)
    p.add_argument('--height',type=int,default=480)
    p.add_argument('--camera-fps',type=int,default=30)
    p.add_argument('--threads',type=int,default=2)
    p.add_argument('--person-backend',choices=('npu','cpu'),default='cpu',
                   help='Person detector backend; Windows defaults to CPU NanoDet')
    p.add_argument('--person-confidence',type=float,default=.35)
    p.add_argument('--person-low-confidence',type=float,default=.10,
                   help='Low-score candidates retain existing tracks only')
    p.add_argument('--reid-model',type=Path,help='Optional verified OSNet x0.25 ONNX; sparse CPU, detector stays NPU')
    p.add_argument('--port',default='')
    p.add_argument('--steering-config',type=Path,default=ROOT/'steering_config.json')
    p.add_argument('--hfov',type=float)
    p.add_argument('--lock-mode',choices=('auto','manual'),default='auto')
    p.add_argument('--single-person-slot',choices=('on','off'),default='on',
                   help='Use slot 1 after continuous single-person confirmation')
    p.add_argument('--no-show',action='store_true')
    p.add_argument('--max-seconds',type=float,default=0.)
    p.add_argument('--metrics-json',type=Path)
    p.add_argument('--trace-jsonl',type=Path,help='Optional local detection/association metadata for validation')
    p.add_argument('--evidence-image',type=Path,help='Optional local screenshot; never stored by default')
    a=p.parse_args()
    if (a.width,a.height) not in ((640,480),(1280,720)) or not 1<=a.threads<=8 or not .1<=a.person_confidence<=.9 or not 0<a.camera_fps<=120 or not 0<=a.max_seconds<float('inf'):
        p.error('Invalid camera/threads/confidence/duration')
    if not .01<=a.person_low_confidence<a.person_confidence:
        p.error('Low confidence must be positive and below high confidence')
    steering=Steering(a.steering_config,a.hfov)
    if steering.intrinsics:
        c=steering.intrinsics
        if abs(a.width/a.height-c['image_width']/c['image_height'])>.01:p.error('Aspect differs from calibration')
    elif a.port and abs(a.width/a.height-4/3)>.01 and a.hfov is None:
        p.error('720p serial steering requires verified --hfov or matching camera calibration')
    show_bearing=not(abs(a.width/a.height-4/3)>.01 and a.hfov is None and not steering.intrinsics)
    cv2.setNumThreads(a.threads)
    worker=camera=output=trace=None
    stop=False
    runtime_error=None
    def shutdown(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,shutdown)
    signal.signal(signal.SIGINT,shutdown)
    encoder=None
    if a.reid_model:
        from body_reid import BodyReID
        encoder=BodyReID(a.reid_model)
    selector=BodySelection();identities=BodyIdentities(high_threshold=a.person_confidence,
                              low_threshold=a.person_low_confidence,reid=encoder);hud=BodyHUD(a.person_backend)
    auto=a.lock_mode=='auto';clicked=[];tracks=[]
    single=SinglePersonPolicy(high=a.person_confidence) if a.single_person_slot=='on' else None
    def mouse(event,x,y,*_):
        if event!=cv2.EVENT_LBUTTONDOWN:return
        point=hud.to_image(x,y)
        if point is None:return
        px,py=point
        for track in tracks:
            if track['person_id']<=0:continue
            x,y,w,h=track['box']
            if x<=px<=x+w and y<=py<=y+h:clicked.append(track['person_id']);break
    # Keep the Qt lookup key ASCII; use a separate localized display title.
    window='BodyLock / Windows CPU Guidance' if a.person_backend=='cpu' else 'BodyLock / NPU Guidance'
    samples=deque(maxlen=18000);quality=[];modes={}
    count=measured=valid_count=0;sum_compute=sum_age=0.;seq=first_seq=0
    valid_start=None;longest=0.;stats={};snapshot=Snapshot()
    start=time.monotonic();last_print=start
    try:
        if a.trace_jsonl:
            a.trace_jsonl.parent.mkdir(parents=True,exist_ok=True)
            trace=a.trace_jsonl.open('w',encoding='utf-8',buffering=1)
        worker=PersonWorker(ROOT,a.person_backend,a.person_low_confidence)
        output=Output(a.port,ROOT/'logs'/f'body_{time.time_ns()}.csv',.4,120,'F2',steering,print_packets=False)
        capture_backend={'auto':cv2.CAP_ANY,'dshow':cv2.CAP_DSHOW,'msmf':cv2.CAP_MSMF}[a.camera_backend]
        camera=LatestCamera(a.camera,a.width,a.height,a.camera_fps,backend=capture_backend)
        print('BODY_ONLY / NO FACE MODEL / BACKEND='+worker.backend_name,flush=True)
        if not a.no_show:
            # Native pixels: avoids resizing small text through Qt and VNC.
            cv2.namedWindow(window,cv2.WINDOW_AUTOSIZE | cv2.WINDOW_GUI_NORMAL)
            # ASCII avoids mojibake in the Windows HighGUI title bar.
            cv2.setWindowTitle(window,'Body Tracking / Steering Guidance')
            cv2.moveWindow(window,10,34);cv2.setMouseCallback(window,mouse)
        start=time.monotonic();last_print=start;meter=PerformanceMeter(start)
        while not stop:
            if a.max_seconds and time.monotonic()-start>=a.max_seconds:break
            # Serial unplug/driver re-enumeration is shown in the HUD and retried
            # by Output; it must not terminate the body-only preview.
            if camera.failed:raise RuntimeError('Camera failed after 15 s USB reconnect timeout')
            frame,captured,frame_seq=camera.latest(seq)
            if frame is None:
                if camera.disconnected:
                    # LatestCamera is attempting to recover a transient USB
                    # reset.  Do not mistake the old frame timestamp for a
                    # stalled camera and exit before the reconnect timeout.
                    time.sleep(.05)
                    continue
                if time.monotonic()-(captured or start)>5:raise RuntimeError('Camera stalled')
                time.sleep(.001);continue
            if not count:first_seq=frame_seq
            seq=frame_seq;t=time.monotonic()
            worker.submit(frame);bodies,body_ms=worker.result();matched=time.monotonic()
            fresh=matched-captured<=.4
            if single:
                tracks=single.update(frame,bodies if fresh else [],captured,identities)
            else:
                tracks=identities.update(frame,bodies if fresh else [],captured)
            if clicked:
                selector.select(clicked[-1]);clicked.clear()
            if auto and single:
                single.auto_select(selector)
            elif auto and not selector.target_id:
                confirmed=[track for track in tracks if track['confirmed'] and track['person_id']>0]
                # Auto selection is only unambiguous with one visible detection.
                if len(confirmed)==1 and len(bodies)==1:selector.select(confirmed[0]['person_id'])
            snapshot=selector.update(tracks if fresh else [],captured,a.width,a.height)
            output.publish(snapshot);done=time.monotonic();fields=control_fields(snapshot,now=done)
            if trace:
                trace.write(json.dumps(dict(t=captured-start,seq=seq,boxes=bodies,tracks=tracks,
                            target=selector.target_id,mode=selector.mode,valid=int(fields['valid'])))+'\n')
            count+=1;appearance_ms=(done-matched)*1000;compute_ms=(done-t)*1000;age_ms=(done-captured)*1000
            meter.add(done,seq,False,True,0.,body_ms,compute_ms,age_ms,bool(fields['valid']))
            stats=meter.read();stats['appearance_ms']=appearance_ms
            stats.update(worker.last_timing)
            if done-start>=2:
                measured+=1;valid_count+=bool(fields['valid']);sum_compute+=compute_ms;sum_age+=age_ms
                samples.append((compute_ms,age_ms,body_ms,appearance_ms,
                                worker.last_timing.get('pre_ms',0.),worker.last_timing.get('npu_and_copy_ms',0.),
                                worker.last_timing.get('post_ms',0.),0.))
                modes[selector.mode]=modes.get(selector.mode,0)+1
                if fields['valid']:
                    if valid_start is None:valid_start=done
                    longest=max(longest,done-valid_start)
                else:valid_start=None
                if len(quality)<60 and (not quality or done-quality[-1]['time']>=1):
                    small=frame[::8,::8];gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
                    quality.append(dict(time=done,mean_luma=float(gray.mean()),color_fraction=float(np.mean(np.ptp(small.astype(np.int16),axis=2)>10)),dark_fraction=float(np.mean(gray<12)),clipped_fraction=float(np.mean(gray>245))))
            if done-last_print>=2:
                print(f"[BODY] FPS={stats['fps']:.2f} CAMERA={stats['camera_fps']:.2f} DETECT={body_ms:.1f}ms MATCH={appearance_ms:.1f}ms TARGET={selector.target_id} MODE={selector.mode} bodies={len(bodies)} tracks={len(tracks)} IDS={identities.counters['public_ids_created']} VALID={stats['valid_percent']:.0f}%",flush=True)
                last_print=done
            canvas=None
            if not a.no_show:
                ui_started=time.monotonic()
                angle=steering.bearing(snapshot) if show_bearing and fields['valid'] else None
                canvas=hud.render(frame,tracks,selector,stats,angle,auto,a.port,done-start,
                                  distance=getattr(output,'distance',None),
                                  serial_error=getattr(output,'serial_error',None))
                cv2.imshow(window,canvas);key=cv2.waitKey(1)&255
                if done-start>=2 and samples:
                    samples[-1]=(*samples[-1][:-1],(time.monotonic()-ui_started)*1000)
                if key in (ord('q'),27) or cv2.getWindowProperty(window,cv2.WND_PROP_VISIBLE)<1:break
                if key==ord('u'):selector.select(0);auto=False
                if key==ord('a'):auto=not auto
                if ord('1')<=key<=ord('9'):
                    pid=key-ord('0')
                    if any(track['person_id']==pid for track in tracks):clicked.append(pid)
            if a.max_seconds and time.monotonic()-start>=a.max_seconds:break
        duration=time.monotonic()-start;measured_duration=max(duration-2,1e-9)
        if a.evidence_image and count:
            a.evidence_image.parent.mkdir(parents=True,exist_ok=True)
            image=frame if a.no_show else canvas
            if image is not None:cv2.imwrite(str(a.evidence_image),image)
        if a.metrics_json:
            result=dict(algorithm='body-byte-association-v2',face_models_loaded=False,registration_required=False,
                biometric_identity=False,gender_inference=False,processed_frames=count,elapsed_seconds=duration,
                warmup_seconds=2,measured_frames=measured,steady_wall_fps=measured/measured_duration,
                observed_capture_fps=(seq-first_seq)/max(duration,1e-9),body_detection_fps=measured/measured_duration,
                valid_percent=100*valid_count/max(measured,1),longest_valid_seconds=longest,
                mean_pipeline_ms=sum_compute/max(measured,1),mean_host_frame_age_ms=sum_age/max(measured,1),
                pipeline_p95_ms=float(np.percentile([s[0] for s in samples],95)) if samples else None,
                host_frame_age_p95_ms=float(np.percentile([s[1] for s in samples],95)) if samples else None,
                capture_width=a.width,capture_height=a.height,capture_channels=3,capture_format='MJPG requested',camera_backend=a.camera_backend,
                backend=worker.backend_name,ui='disabled' if a.no_show else 'native960x660',target_id=selector.target_id,
                mode_frame_counts=modes,quality_samples=[{k:v for k,v in s.items() if k!='time'} for s in quality],
                serial_enabled=bool(a.port),serial_error=(output.serial_error if output else None),
                steering_enabled=True,source_for_valid_body=2,threads=a.threads,person_confidence=a.person_confidence,
                person_low_confidence=a.person_low_confidence,tracking=identities.metrics(),
                single_person=single.metrics() if single else None,
                stages={name:dict(mean_ms=float(np.mean([s[index] for s in samples])),
                                 p95_ms=float(np.percentile([s[index] for s in samples],95)))
                        for index,name in enumerate(('pipeline','frame_age','detection','association',
                                                      'preprocess','npu_and_copy','postprocess','ui'))} if samples else {},
                final_window=stats)
            a.metrics_json.parent.mkdir(parents=True,exist_ok=True)
            a.metrics_json.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print('METRICS_SAVED',a.metrics_json,flush=True)
    except Exception as exc:
        # Keep VNC launches diagnosable: an uncaught exception otherwise looks
        # like a window that simply flashed and disappeared.
        runtime_error=exc
        print(f'程序异常退出: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
        raise
    finally:
        if output:output.close()
        if camera:camera.close()
        if worker:worker.close()
        if trace:trace.close()
        if not a.no_show:cv2.destroyAllWindows()


if __name__=='__main__':main()
