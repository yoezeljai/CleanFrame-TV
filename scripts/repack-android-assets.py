"""Swap new page files into a built Fire TV APK and re-sign it, without Java or the Android SDK.

For updates that only touch the web page (app/, android/device-android.js): run
scripts/build-android.sh far enough to refresh dist/android/assets/www (it stops at aapt2
if the SDK is absent), then:

  python3 scripts/repack-android-assets.py dist/CleanFrame-firetv.apk dist/android/assets/www

The APK is rewritten in place with a JAR (v1) signature from .local/android/cleanframe.keystore
(password in .local/android/keystore.pass),
which Fire OS 5 (Android 5.1) accepts. Java or manifest changes still need build-android.sh.
"""
import base64
import hashlib
import sys
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12, pkcs7

ROOT = Path(__file__).resolve().parents[1]
KEYSTORE, PASSWORD_FILE = ROOT / '.local/android/cleanframe.keystore', ROOT / '.local/android/keystore.pass'


def manifest_line(text):
    """Manifest lines are at most 72 bytes; longer ones continue with a leading space."""
    raw, out = text.encode(), []
    out.append(raw[:70])
    raw = raw[70:]
    while raw:
        out.append(b' ' + raw[:69])
        raw = raw[69:]
    return b'\r\n'.join(out) + b'\r\n'


def b64sha(data):
    return base64.b64encode(hashlib.sha256(data).digest()).decode()


def main(apk, www):
    apk, www = Path(apk), Path(www)
    old = zipfile.ZipFile(apk)
    entries = []
    for info in old.infolist():
        if info.filename.startswith(('META-INF/', 'assets/www/')):
            continue
        entries.append((info.filename, old.read(info), info.compress_type))
    for f in sorted(p for p in www.rglob('*') if p.is_file()):
        name = 'assets/www/' + f.relative_to(www).as_posix()
        stored = f.suffix in ('.jpg', '.png', '.woff2')
        entries.append((name, f.read_bytes(), zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED))
    old.close()

    mf_head = b'Manifest-Version: 1.0\r\nCreated-By: CleanFrame repack\r\n\r\n'
    sections = [manifest_line('Name: ' + n) + manifest_line('SHA-256-Digest: ' + b64sha(d)) + b'\r\n' for n, d, _ in entries]
    manifest = mf_head + b''.join(sections)
    sf = (b'Signature-Version: 1.0\r\nCreated-By: CleanFrame repack\r\n'
          + manifest_line('SHA-256-Digest-Manifest: ' + b64sha(manifest))
          + manifest_line('SHA-256-Digest-Manifest-Main-Attributes: ' + b64sha(mf_head)) + b'\r\n')
    for (n, _, _), section in zip(entries, sections):
        sf += manifest_line('Name: ' + n) + manifest_line('SHA-256-Digest: ' + b64sha(section)) + b'\r\n'

    key, cert, _ = pkcs12.load_key_and_certificates(KEYSTORE.read_bytes(), PASSWORD_FILE.read_text().strip().encode())
    sig = (pkcs7.PKCS7SignatureBuilder().set_data(sf).add_signer(cert, key, hashes.SHA256())
           .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.NoAttributes]))

    tmp = apk.with_suffix('.tmp.apk')
    with zipfile.ZipFile(tmp, 'w') as out:
        out.writestr('META-INF/MANIFEST.MF', manifest, zipfile.ZIP_DEFLATED)
        out.writestr('META-INF/CLEANFRA.SF', sf, zipfile.ZIP_DEFLATED)
        out.writestr('META-INF/CLEANFRA.RSA', sig, zipfile.ZIP_DEFLATED)
        for n, d, c in entries:
            out.writestr(zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0)), d, c)
    tmp.replace(apk)
    print('Repacked %s: %d files, signed with %s' % (apk, len(entries), cert.subject.rfc4514_string()))


if __name__ == '__main__':
    main(*sys.argv[1:3])
