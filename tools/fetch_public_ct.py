"""Fetch the optional public CT sample. Never required by tests or CI."""
import hashlib
from pathlib import Path
import urllib.request

SHA256 = '6a5b6caccb76576a863beb095e3bfb910c50ca78f4c9bf043aa42f976cfa53d1'
URL = 'https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/' + SHA256
DESTINATION = Path(__file__).resolve().parents[1] / 'data/downloads/CT-brain.nrrd'


def main():
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists():
        if hashlib.sha256(DESTINATION.read_bytes()).hexdigest() == SHA256:
            print(f'Already present and checksum verified: {DESTINATION}')
            return
        raise ValueError('Existing file has wrong checksum. Move it aside before retrying.')
    temporary = DESTINATION.with_suffix('.download')
    digest, total = hashlib.sha256(), 0
    request = urllib.request.Request(URL, headers={'User-Agent': 'bone-defect-planner-learning-prototype/0.1'})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as stream:
        while chunk := response.read(1024*1024):
            total += len(chunk)
            if total > 40*1024*1024:
                raise ValueError('Unexpected download larger than 40 MiB')
            digest.update(chunk)
            stream.write(chunk)
    if digest.hexdigest() != SHA256:
        raise ValueError('Checksum mismatch. Download is not accepted.')
    temporary.replace(DESTINATION)
    print(f'Downloaded {total} bytes; SHA256 verified: {DESTINATION}')


if __name__ == '__main__':
    main()
