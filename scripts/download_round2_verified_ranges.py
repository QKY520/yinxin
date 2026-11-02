#!/usr/bin/env python3
"""No-card bounded parallel download; immutable chunks, final vendor digest required."""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import time
import threading
import ssl
import urllib.request
import urllib.parse
from pathlib import Path


def digest(path, algorithm):
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',required=True);p.add_argument('--target',required=True,type=Path)
    p.add_argument('--size',required=True,type=int);p.add_argument('--sha256');p.add_argument('--md5')
    p.add_argument('--chunk-bytes',type=int,default=4*1024*1024)
    p.add_argument('--workers',type=int,default=8)
    args=p.parse_args()
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    assert args.sha256 or args.md5
    assert 64*1024 <= args.chunk_bytes <= 4*1024*1024 and 1 <= args.workers <= 32
    target=args.target.resolve()
    allowed=[Path('/root/autodl-tmp/models/uie-base-round2-official'),Path('/root/autodl-tmp/round2_uie_nocard_20261010/gpu_wheelhouse')]
    assert any(target.is_relative_to(base) for base in allowed)
    target.parent.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(target.parent).free>max(2*args.size,2*1024**3)
    assert not target.exists(), 'Never overwrite a completed resource'
    chunks=target.parent/(target.name+'.range_chunks')
    chunks.mkdir(exist_ok=True)
    ranges=[(i,a,min(a+args.chunk_bytes,args.size)-1) for i,a in enumerate(range(0,args.size,args.chunk_bytes))]
    cached=[]
    for path in chunks.glob('*.bin'):
        _,a,b=map(int,path.stem.split('_'))
        assert path.stat().st_size==b-a+1
        cached.append((a,b,path))
    sessions=threading.local()
    def fetch(item):
        i,a,b=item
        good=chunks/f'{i:04d}_{a}_{b}.bin'
        if good.exists():
            assert good.stat().st_size==b-a+1
            return
        for old_a,old_b,path in cached:
            if old_a <= a <= b <= old_b:
                with path.open('rb') as source,good.open('xb') as output:
                    source.seek(a-old_a)
                    output.write(source.read(b-a+1))
                assert good.stat().st_size==b-a+1
                return
        errors=[]
        for attempt in range(1,5):
            part=chunks/f'{i:04d}_{a}_{b}_attempt{attempt:02d}_{time.time_ns()}.partial'
            try:
                # Reuse a connection per worker instead of a new TLS tunnel for
                # every small range. Final vendor digest still guards all bytes.
                if not hasattr(sessions,'client'):
                    import requests
                    sessions.client=requests.Session()
                    sessions.client.trust_env=False
                    host=urllib.parse.urlsplit(args.url).hostname
                    sessions.client.proxies={} if urllib.request.proxy_bypass(host) else {k:v for k,v in urllib.request.getproxies().items() if k in ['http','https']}
                    # AutoDL's configured academic proxy CA is in the system
                    # trust store. Retain certificate verification; never use False.
                    system_ca=ssl.get_default_verify_paths().cafile
                    assert system_ca and Path(system_ca).is_file(), 'System TLS trust store required'
                    sessions.client.verify=system_ca
                with sessions.client.get(args.url,headers={'Range':f'bytes={a}-{b}'},stream=True,timeout=60) as r:
                    r.raise_for_status()
                    assert r.status_code==206 and r.headers.get('Content-Range')==f'bytes {a}-{b}/{args.size}'
                    with part.open('xb') as out:
                        for block in r.iter_content(64*1024):
                            out.write(block)
                assert part.stat().st_size==b-a+1
                part.rename(good)
                print('CHUNK_OK',i,flush=True)
                return
            except Exception as exc:
                errors.append(f'{type(exc).__name__}: {exc}')
                print('CHUNK_RETRY',i,attempt,errors[-1],flush=True)
        raise RuntimeError({'range':item,'errors':errors})
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(fetch,ranges))
    assembled=target.parent/(target.name+'.assembled.partial')
    with assembled.open('xb') as output:
        for i,a,b in ranges:
            with (chunks/f'{i:04d}_{a}_{b}.bin').open('rb') as f:shutil.copyfileobj(f,output,length=1024*1024)
    assert assembled.stat().st_size==args.size
    if args.sha256:assert digest(assembled,'sha256')==args.sha256, 'Vendor SHA mismatch; partial retained'
    if args.md5:assert digest(assembled,'md5')==args.md5, 'Vendor MD5 mismatch; partial retained'
    assembled.rename(target)
    report={'url':args.url,'bytes':args.size,'sha256':digest(target,'sha256'),'md5':digest(target,'md5'),'model_calls':0}
    with (target.parent/(target.name+'.download.json')).open('x') as f:json.dump(report,f,indent=2)
    print('VENDOR_HASH_PASS',json.dumps(report),flush=True)


if __name__=='__main__':main()
