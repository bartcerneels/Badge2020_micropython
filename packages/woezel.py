import sys
import gc
import uos as os
import uerrno as errno
import ujson as json
import uzlib
import upip_utarfile as tarfile
import consts
gc.collect()

debug = False
install_path = None
cleanup_files = []
gzdict_sz = 16 + 15

file_buf = bytearray(512)

class NotFoundError(Exception):
    pass

class LatestInstalledError(Exception):
    pass

def op_split(path):
    if path == "":
        return ("", "")
    r = path.rsplit("/", 1)
    if len(r) == 1:
        return ("", path)
    head = r[0]
    if not head:
        head = "/"
    return (head, r[1])

def op_basename(path):
    return op_split(path)[1]

# Expects *file* name
def _makedirs(name, mode=0o777):
    ret = False
    s = ""
    comps = name.rstrip("/").split("/")[:-1]
    if comps[0] == "":
        s = "/"
    for c in comps:
        if s and s[-1] != "/":
            s += "/"
        s += c
        try:
            os.mkdir(s)
            ret = True
        except OSError as e:
            if e.args[0] != errno.EEXIST and e.args[0] != errno.EISDIR:
                raise
            ret = False
    return ret


def save_file(fname, subf):
    global file_buf
    with open(fname, "wb") as outf:
        while True:
            sz = subf.readinto(file_buf)
            if not sz:
                break
            outf.write(file_buf, sz)

def install_tar(f, prefix):
    meta = {}
    for info in f:
        #print(info)
        fname = info.name
        try:
            fname = fname[fname.index("/") + 1:]
        except ValueError:
            fname = ""

        save = True
        for p in ("setup.", "PKG-INFO", "README"):
                #print(fname, p)
                if fname.startswith(p) or ".egg-info" in fname:
                    if fname.endswith("/requires.txt"):
                        meta["deps"] = f.extractfile(info).read()
                    save = False
                    if debug:
                        print("Skipping", fname)
                    break

        if save:
            outfname = prefix + fname
            if info.type != tarfile.DIRTYPE:
                if debug:
                    print("Extracting " + outfname)
                _makedirs(outfname)
                subf = f.extractfile(info)
                save_file(outfname, subf)
    return meta

def expandhome(s):
    if "~/" in s:
        h = os.getenv("HOME")
        s = s.replace("~/", h + "/")
    return s

import ussl
import usocket
def url_open(url):
    if debug:
        print(url)
    
    # Enforce Letsencrypt certificate checking
    # ussl.verify_letsencrypt(True)

    proto, _, host, urlpath = url.split('/', 3)
    try:
        ai = usocket.getaddrinfo(host, 443)
    except OSError as e:
        fatal("Unable to resolve %s (no Internet?)" % host, e)
    #print("Address infos:", ai)
    if len(ai) == 0:
        fatal("Unable to resolve %s (no Internet?)" % host, errno.EHOSTUNREACH)
    addr = ai[0][4]

    s = usocket.socket(ai[0][0])
    try:
        #print("Connect address:", addr)
        s.connect(addr)

        if proto == "https:":
            s = ussl.wrap_socket(s, server_hostname=host)

        # MicroPython rawsocket module supports file interface directly
        s.write("GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (urlpath, host))
        l = s.readline()
        protover, status, msg = l.split(None, 2)
        if status != b"200":
            if status == b"404" or status == b"301":
                raise NotFoundError("Package not found")
            raise ValueError(status)
        while 1:
            l = s.readline()
            if not l:
                raise ValueError("Unexpected EOF in HTTP headers")
            if l == b'\r\n':
                break
    except Exception as e:
        s.close()
        raise e

    return s


def get_pkg_metadata(name):
    f = url_open("https://{}/eggs/get/{}/json".format(consts.WOEZEL_WEB_SERVER, name))
    try:
        return json.load(f)
    finally:
        f.close()

def get_pkg_list():
    f = url_open("https://{}/basket/{}/list/json".format(consts.WOEZEL_WEB_SERVER, consts.INFO_HARDWARE_WOEZEL_NAME))
    try:
        return json.load(f)
    finally:
        f.close()

def search_pkg_list(query):
    f = url_open("https://{}/basket/{}/search/{}/json".format(consts.WOEZEL_WEB_SERVER, consts.INFO_HARDWARE_WOEZEL_NAME, query))
    try:
        return json.load(f)
    finally:
        f.close()

def fatal(msg, exc=None):
    print("Error:", msg)
    if exc and debug:
        raise exc
    sys.exit(1)

def install_pkg(pkg_spec, install_path, force_reinstall):
    data = get_pkg_metadata(pkg_spec)
    already_installed = False
    try:
        os.stat("%s%s/" % (install_path, pkg_spec))
    except OSError as e:
        if e.args[0] == errno.EINVAL:
            print("Package %s already installed" % (pkg_spec))
            already_installed = True
        else:
            print("Package %s not yet installed" % (pkg_spec))
    else:
        # fallback for unix version
        print("Package %s already installed" % (pkg_spec))
        already_installed = True
    latest_ver = data["info"]["version"]
    verf = "%s%s/version" % (install_path, pkg_spec)
    if already_installed:
        try:
            with open(verf, "r") as fver:
                old_ver = fver.read()
        except:
            print("No version file found")
        else:
            if old_ver == latest_ver:
                if not force_reinstall:
                    raise LatestInstalledError("Latest version installed")
            else:
                print("Removing previous rev. %s" % old_ver)
                for rm_file in os.listdir("%s%s" % (install_path, pkg_spec)):
                    os.remove("%s%s/%s" % (install_path, pkg_spec, rm_file))
    packages = data["releases"][latest_ver]
    del data
    gc.collect()
    assert len(packages) == 1
    package_url = packages[0]["url"]
    print("Installing %s rev. %s from %s" % (pkg_spec, latest_ver, package_url))
    package_fname = op_basename(package_url)
    f1 = url_open(package_url)
    try:
        f2 = uzlib.DecompIO(f1, gzdict_sz)
        f3 = tarfile.TarFile(fileobj=f2)
        meta = install_tar(f3, "%s%s/" % (install_path, pkg_spec))
    finally:
        f1.close()
    del f3
    del f2
    with open(verf, "w") as fver:
        fver.write(latest_ver)
    del fver
    gc.collect()
    return meta

def install(to_install, install_path=None, force_reinstall=False):
    # Calculate gzip dictionary size to use
    global gzdict_sz
    sz = gc.mem_free() + gc.mem_alloc()
    if sz <= 65536:
        # this will probably give errors with some packages, but we
        # just don't have enough memory.
        gzdict_sz = 16 + 13

    if install_path is None:
        install_path = get_install_path()
    if install_path[-1] != "/":
        install_path += "/"
    if not isinstance(to_install, list):
        to_install = [to_install]
    print("Installing to: " + install_path)
    # sets would be perfect here, but don't depend on them
    installed = []
    try:
        while to_install:
            if debug:
                print("Queue:", to_install)
            pkg_spec = to_install.pop(0)
            if pkg_spec in installed:
                continue
            meta = install_pkg(pkg_spec, install_path, force_reinstall)
            installed.append(pkg_spec)
            if debug:
                print(meta)
            deps = meta.get("deps", "").rstrip()
            if deps:
                deps = deps.decode("utf-8").split("\n")
                to_install.extend(deps)
    except Exception as e:
        print("Error installing '{}': {}, packages may be partially installed".format(
                pkg_spec, e),
            file=sys.stderr)
        raise e

def display_pkg(packages):
    for package in packages:
        print(package["name"])
        print("  Slug:        " + package["slug"])
        print("  Version:     " + package["revision"])
        print("  Description: " + package["description"])


def search(query="*"):
    if query == "*":
        packages = get_pkg_list()
    else:
        packages = search_pkg_list(query)
    display_pkg(packages)

def get_install_path():
    global install_path
    if install_path is None:
        # sys.path[0] is current module's path
        install_path = sys.path[1]
    install_path = expandhome(install_path)
    return install_path

def cleanup():
    for fname in cleanup_files:
        try:
            os.unlink(fname)
        except OSError:
            print("Warning: Cannot delete " + fname)

def main():
    global debug
    global install_path
    install_path = None

    if len(sys.argv) < 2 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        help()
        return

    if sys.argv[1] != "install":
        fatal("Only 'install' command supported")

    to_install = []

    i = 2
    while i < len(sys.argv) and sys.argv[i][0] == "-":
        opt = sys.argv[i]
        i += 1
        if opt == "-h" or opt == "--help":
            help()
            return
        elif opt == "-p":
            install_path = sys.argv[i]
            i += 1
        elif opt == "-r":
            list_file = sys.argv[i]
            i += 1
            with open(list_file) as f:
                while True:
                    l = f.readline()
                    if not l:
                        break
                    if l[0] == "#":
                        continue
                    to_install.append(l.rstrip())
        elif opt == "--debug":
            debug = True
        else:
            fatal("Unknown/unsupported option: " + opt)

    to_install.extend(sys.argv[i:])
    if not to_install:
        help()
        return

    install(to_install)

    if not debug:
        cleanup()


if __name__ == "__main__":
    main()
