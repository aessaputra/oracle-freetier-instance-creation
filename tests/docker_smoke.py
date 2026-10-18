"""Build first: docker build -t oci-launcher:test .; then run this offline check."""
import subprocess
import uuid


image = "oci-launcher:test"
volume = "oci-launcher-smoke-" + uuid.uuid4().hex
probe = r'''
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import paramiko

assert os.getuid() == 10001
assert Path.cwd() == Path('/data')
assert not Path('/app/oci.env').exists()
key = paramiko.RSAKey.generate(2048)
key.write_private_key_file('/data/offline-api.pem')
Path('/data/offline-config').write_text(
    '[DEFAULT]\nuser=ocid1.user.oc1..offline\n'
    'tenancy=ocid1.tenancy.oc1..offline\n'
    'fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00\n'
    'region=us-ashburn-1\nkey_file=/data/offline-api.pem\n'
)
os.environ['OCI_CONFIG'] = '/data/offline-config'
os.environ['SSH_AUTHORIZED_KEYS_FILE'] = '/data/ssh/instance.pub'
os.environ['NOTIFY_EMAIL'] = 'False'
os.environ['DISCORD_WEBHOOK'] = ''
app = runpy.run_path('/app/main.py', run_name='offline_smoke')
public_key = app['read_or_generate_ssh_public_key']('/data/ssh/instance.pub')
assert public_key.startswith('ssh-rsa ')
assert app['read_or_generate_ssh_public_key']('/data/ssh/instance.pub') == public_key
instance = SimpleNamespace(id='offline-instance', display_name='offline-test',
    availability_domain='AD-1', shape=app['ARM_SHAPE'], lifecycle_state='RUNNING')
app['create_instance_details_file_and_notify'](instance)
assert 'offline-instance' in Path('/data/INSTANCE_CREATED').read_text()
assert 'offline-test' in app['generate_html_body'](instance)
print('PASS: non-root runtime, dependencies, OCI client initialization, HTML, SSH keys, output files')
'''

try:
    subprocess.run(['docker', 'volume', 'create', volume], check=True, capture_output=True)
    base = ['docker', 'run', '--rm', '--network', 'none',
            '--mount', f'type=volume,source={volume},target=/data', image, 'python', '-c']
    subprocess.run(base + [probe], check=True)
    subprocess.run(base + [
        "from pathlib import Path; "
        "assert 'offline-instance' in Path('/data/INSTANCE_CREATED').read_text(); "
        "assert Path('/data/ssh/instance_private').is_file(); "
        "assert Path('/data/launch_instance.log').is_file(); "
        "print('PASS: output, logs and SSH private key survive container replacement')"
    ], check=True)
finally:
    subprocess.run(['docker', 'volume', 'rm', volume], check=True, capture_output=True)
