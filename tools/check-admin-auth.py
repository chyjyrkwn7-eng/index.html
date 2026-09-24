"""Does the admin auth path actually produce a valid RS256 JWT?

No network: a throwaway key is generated here, the tool signs an
assertion with it, and the signature is verified with openssl. That
covers everything except Google accepting the token, which only a real
key can test.
"""
import base64, importlib.util, json, os, subprocess, sys, tempfile, time

spec = importlib.util.spec_from_file_location(
    "fa", os.path.join(os.path.dirname(os.path.abspath(__file__)), "firestore-admin.py"))
fa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fa)

tmp = tempfile.mkdtemp()
priv = os.path.join(tmp, "k.pem")
pub = os.path.join(tmp, "k.pub")
subprocess.run(["openssl", "genrsa", "-out", priv, "2048"],
               check=True, stderr=subprocess.DEVNULL)
subprocess.run(["openssl", "rsa", "-in", priv, "-pubout", "-out", pub],
               check=True, stderr=subprocess.DEVNULL)
pem = open(priv).read()

# 1. no key configured -> anonymous, and it must say so rather than crash
os.environ.pop("NOVA_ADMIN_KEY", None)
os.environ.pop("NOVA_ADMIN_KEY_FILE", None)
print("no key -> _load_key():", fa._load_key())
assert fa._load_key() is None

# 2. a key from the env var is parsed
fake = {"client_email": "nova@example.iam.gserviceaccount.com",
        "private_key": pem, "token_uri": "https://oauth2.googleapis.com/token"}
os.environ["NOVA_ADMIN_KEY"] = json.dumps(fake)
got = fa._load_key()
print("env key -> client_email:", got["client_email"])
assert got and got["client_email"] == fake["client_email"]

# 3. a key from a FILE is parsed too
os.environ.pop("NOVA_ADMIN_KEY")
kf = os.path.join(tmp, "key.json")
open(kf, "w").write(json.dumps(fake))
os.environ["NOVA_ADMIN_KEY_FILE"] = kf
assert fa._load_key() is not None
print("file key -> ok")

# 4. junk in the env var must not crash the tool
os.environ["NOVA_ADMIN_KEY"] = "not json at all"
os.environ.pop("NOVA_ADMIN_KEY_FILE")
assert fa._load_key() is None
print("junk key -> None, no crash")

# 5. THE REAL CHECK: the signature verifies against the public key.
msg = (fa._b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
       + b"." + fa._b64(json.dumps({"iss": "x", "exp": int(time.time()) + 60}).encode()))
sig = fa._sign_rs256(msg, pem)
sigfile = os.path.join(tmp, "sig.bin")
open(sigfile, "wb").write(sig)
p = subprocess.run(["openssl", "dgst", "-sha256", "-verify", pub,
                    "-signature", sigfile],
                   input=msg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = p.stdout.decode().strip()
print("signature verify ->", out)
assert "Verified OK" in out

# 6. and the assertion is a well-formed JWT: three parts, decodable halves
parts = (msg + b"." + fa._b64(sig)).split(b".")
assert len(parts) == 3
hdr = json.loads(base64.urlsafe_b64decode(parts[0] + b"=" * (-len(parts[0]) % 4)))
print("jwt header ->", hdr)
assert hdr["alg"] == "RS256"

# 7. the private key must never be left lying around in a temp file
leftovers = [f for f in os.listdir(tempfile.gettempdir())
             if f.endswith(".pem") and f != os.path.basename(priv)]
print("stray .pem files left by signing:", leftovers)
assert not leftovers

# 8. THE PURE-PYTHON SIGNER MUST MATCH OPENSSL BYTE FOR BYTE.
# It is the only path that works on an iPad (iOS forbids spawning a
# process, so a-Shell has no openssl and cannot build a crypto
# library). "It produced some bytes" is not a check - a wrong
# signature fails as a 400 from Google with nothing to say why, so
# this compares it against the reference implementation directly.
ref = subprocess.run(["openssl", "dgst", "-sha256", "-sign", priv],
                     input=msg, stdout=subprocess.PIPE).stdout
pure = fa._sign_rs256_pure(msg, pem)
print("pure-python signature == openssl:", pure == ref,
      "(%d bytes)" % len(pure))
assert pure == ref, "pure signer disagrees with openssl"

# and it must verify as a signature in its own right
pf = os.path.join(tmp, "pure.bin")
open(pf, "wb").write(pure)
v = subprocess.run(["openssl", "dgst", "-sha256", "-verify", pub,
                    "-signature", pf],
                   input=msg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("pure signature verifies ->", v.stdout.decode().strip())
assert "Verified OK" in v.stdout.decode()

# 9. the PKCS#8 key Google actually issues, and a PKCS#1 one
n8, d8 = fa._rsa_from_pem(pem)
p1 = subprocess.run(["openssl", "rsa", "-in", priv, "-traditional"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode()
if p1.strip():
    n1, d1 = fa._rsa_from_pem(p1)
    print("PKCS#8 and PKCS#1 parse to the same key:", (n8, d8) == (n1, d1))
    assert (n8, d8) == (n1, d1)
assert n8.bit_length() >= 2040, "modulus looks wrong: %d bits" % n8.bit_length()
print("modulus parsed:", n8.bit_length(), "bits")

print("\nALL PASS - signing, key loading and JWT shape are correct.")
print("Untested without a real key: Google accepting the token, and the")
print("progress listing coming back 200 instead of 403.")


def check_two_field_env():
    """The two-field route, which is the only one a person with no
    terminal can actually use. The environment-variable box takes one
    NAME=value per line, so a thirty-line JSON key file cannot go in it
    at all - reported as `couldn't parse "{" - use key=value format`.
    Both fields below are already single lines inside that file."""
    import importlib.util as _il
    spec = _il.spec_from_file_location("_fa", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "firestore-admin.py"))
    fa = _il.module_from_spec(spec); spec.loader.exec_module(fa)
    saved = {k: os.environ.pop(k, None) for k in
             ("NOVA_ADMIN_EMAIL", "NOVA_ADMIN_PRIVATE_KEY",
              "NOVA_ADMIN_KEY", "NOVA_ADMIN_KEY_FILE")}
    fails = []
    try:
        if fa._load_key() is not None:
            fails.append("a bare environment is not anonymous")
        # A form usually delivers the escapes as two characters.
        os.environ["NOVA_ADMIN_EMAIL"] = "a@b.iam.gserviceaccount.com"
        os.environ["NOVA_ADMIN_PRIVATE_KEY"] = (
            "-----BEGIN PRIVATE KEY-----\\nAAAA\\n-----END PRIVATE KEY-----\\n")
        k = fa._load_key()
        if not k or k.get("client_email") != "a@b.iam.gserviceaccount.com":
            fails.append("the two-field route did not load")
        elif "\\n" in k["private_key"] or "\n" not in k["private_key"]:
            fails.append("backslash-n was not turned into a real newline")
        # THE REAL TEST IS THAT THE KEY STILL PARSES, not how many
        # newlines survived - _load_key strips the trailing one, which
        # is correct and which an earlier version of this check called a
        # failure. So a genuine 2048-bit key goes through the two-field
        # route both ways and has to come out as the same modulus the
        # PEM itself parses to.
        want_n, want_d = fa._rsa_from_pem(pem)
        for label, blob in (("real newlines", pem),
                            ("backslash-n escapes", pem.replace("\n", "\\n"))):
            os.environ["NOVA_ADMIN_PRIVATE_KEY"] = blob
            k2 = fa._load_key()
            try:
                got = fa._rsa_from_pem(k2["private_key"]) if k2 else None
            except Exception as e:
                got = "raised: %s" % e
            if got != (want_n, want_d):
                fails.append("a real key pasted with %s did not parse" % label)
        # Half of it set is an error, not a silent anonymous run - that
        # is exactly the case somebody lands in after one failed paste.
        del os.environ["NOVA_ADMIN_PRIVATE_KEY"]
        if fa._load_key() is not None:
            fails.append("half the credentials read as a whole key")
    finally:
        for k2, v in saved.items():
            os.environ.pop(k2, None)
            if v is not None:
                os.environ[k2] = v
    print("\ntwo-field env (NOVA_ADMIN_EMAIL + NOVA_ADMIN_PRIVATE_KEY):")
    for f in fails:
        print("  FAIL", f)
    if not fails:
        print("  PASS both fields load, escapes and real newlines both work,"
              "\n       and half a pair is refused rather than half-used")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(check_two_field_env())
