# For an installation in a virtual python environment
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Use Distribution packages for BCC. They are not provided
# via pip at the moment.

apt install python3-bpfcc
cp -av /usr/lib/python3/dist-packages/bcc* .venv/lib/python3.9/site-packages/
```

## Run tests
```shell
python -m unittest discover
```