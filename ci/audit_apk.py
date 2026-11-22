#!/usr/bin/env python3
"""Аудит собранного APK: то, что нельзя проверить юнит-тестами.

Использование: python3 ci/audit_apk.py <apk> [--report файл.md] [--signer-file файл]
Нужны aapt2 и apksigner из Android build-tools (ANDROID_HOME) и keytool (JDK).
Код выхода 1 — есть нарушения (FAIL); предупреждения (WARN) сборку не валят.
"""
import glob
import os
import re
import struct
import subprocess
import sys
import zipfile

PACKAGE = "app.codeacademy"
MIN_SDK, TARGET_SDK = 26, 35
# Приложение работает без сети и без доступа к личным данным: любые из этих разрешений — нарушение.
FORBIDDEN = {
    "android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE", "android.permission.ACCESS_WIFI_STATE",
    "android.permission.CAMERA", "android.permission.RECORD_AUDIO", "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS", "android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.MANAGE_EXTERNAL_STORAGE",
    "android.permission.READ_SMS", "android.permission.SEND_SMS", "android.permission.READ_PHONE_STATE", "android.permission.READ_CALL_LOG",
    "android.permission.SYSTEM_ALERT_WINDOW", "android.permission.REQUEST_INSTALL_PACKAGES", "android.permission.QUERY_ALL_PACKAGES",
}
EXPORTED_ALLOWED = {".MainActivity", PACKAGE + ".MainActivity"}
# Компоненты библиотек, открытые наружу, но защищённые системным разрешением (достучаться может только оболочка adb/система):
# ProfileInstallReceiver (AndroidX profileinstaller) принимает команды только при разрешении DUMP.
EXPORTED_PROTECTED = {"androidx.profileinstaller.ProfileInstallReceiver": "android.permission.DUMP"}
ANDROID_NS = "http://schemas.android.com/apk/res/android"

results = []  # (статус, текст)


def check(ok, name, detail="", warn_only=False):
    status = "PASS" if ok else ("WARN" if warn_only else "FAIL")
    results.append((status, name + (f": {detail}" if detail else "")))
    return ok


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def find_tool(name):
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or ""
    cands = sorted(glob.glob(os.path.join(home, "build-tools", "*", name)), key=lambda p: [int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", p.split("build-tools")[1])])
    return cands[-1] if cands else name


# ---------- манифест ----------
def parse_xmltree(text):
    """Разбор вывода `aapt2 dump xmltree`: список элементов с атрибутами и вложенностью."""
    elems, stack = [], []
    for line in text.splitlines():
        m = re.match(r"^(\s*)E: ([\w.:-]+)", line)
        if m:
            depth = len(m.group(1))
            while stack and stack[-1][0] >= depth:
                stack.pop()
            el = {"tag": m.group(2), "attrs": {}, "parent": stack[-1][1] if stack else None}
            elems.append(el)
            stack.append((depth, el))
            continue
        m = re.match(r"^\s*A: (?:[^=]*?:)?([\w.-]+)(?:\(0x[0-9a-fA-F]+\))?=(.*)$", line)
        if m and stack:
            stack[-1][1]["attrs"][m.group(1)] = clean_value(m.group(2))
    return elems


def clean_value(v):
    v = v.strip()
    raw = re.search(r'\(Raw: "(.*)"\)\s*$', v)
    if raw:
        return raw.group(1)
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    return v


def truthy(v):
    return v in ("true", "(type 0x12)0xffffffff", "0xffffffff", "-1")


def falsy(v):
    return v in ("false", "(type 0x12)0x0", "0x0", "0")


def audit_manifest(aapt2, apk):
    out = run([aapt2, "dump", "xmltree", "--file", "AndroidManifest.xml", apk])
    if out.returncode != 0 or "E: manifest" not in out.stdout:
        check(False, "Манифест читается", (out.stderr or out.stdout)[:200])
        return
    elems = parse_xmltree(out.stdout)
    app = next((e for e in elems if e["tag"] == "application"), None)
    check(app is not None, "Есть элемент application")
    if not app:
        return
    a = app["attrs"]
    check(falsy(a.get("debuggable", "false")), "Релиз не debuggable", f"debuggable={a.get('debuggable', 'нет (по умолчанию false)')}")
    check(falsy(a.get("allowBackup", "true")), "allowBackup=false (данные не утекают через adb/облачный бэкап)", f"allowBackup={a.get('allowBackup', 'нет (по умолчанию true)')}")
    check("icon" in a and "roundIcon" in a, "Иконка и круглая иконка заданы", f"icon={a.get('icon')}, roundIcon={a.get('roundIcon')}")
    check(not truthy(a.get("usesCleartextTraffic", "false")), "Нет usesCleartextTraffic=true")
    exported = []
    for e in elems:
        if e["tag"] in ("activity", "activity-alias", "service", "receiver", "provider"):
            name = e["attrs"].get("name", "?")
            has_filter = any(c["tag"] == "intent-filter" and c["parent"] is e for c in elems)
            is_exp = truthy(e["attrs"].get("exported", "false" if not has_filter else "true"))
            if is_exp:
                if EXPORTED_PROTECTED.get(name) and e["attrs"].get("permission") == EXPORTED_PROTECTED[name]:
                    results.append(("INFO", f"Открыт наружу, но защищён разрешением {e['attrs'].get('permission')}: {name}"))
                    continue
                exported.append(name)
    extra = [n for n in exported if n not in EXPORTED_ALLOWED]
    check(not extra, "Наружу открыта только главная Activity", f"лишние: {extra}" if extra else f"открыта: {exported}")
    perms = [e["attrs"].get("name", "?") for e in elems if e["tag"].startswith("uses-permission")]
    bad = sorted(set(perms) & FORBIDDEN)
    check(not bad, "Нет запрещённых разрешений (сеть, личные данные, хранилище)", f"найдены: {bad}" if bad else f"всего разрешений: {len(perms)}")
    results.append(("INFO", "Разрешения: " + (", ".join(sorted(perms)) or "нет")))
    for svc in ("MentorService", "RunnerService", "IsolatedRunnerService"):
        check(any(e["tag"] == "service" and e["attrs"].get("name", "").endswith(svc) for e in elems), f"Служба {svc} объявлена")


def audit_badging(aapt2, apk):
    out = run([aapt2, "dump", "badging", apk]).stdout
    pkg = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", out)
    check(bool(pkg) and pkg.group(1) == PACKAGE, "Идентификатор приложения", pkg.group(1) if pkg else "не найден")
    if pkg:
        results.append(("INFO", f"Версия: {pkg.group(3)} (versionCode {pkg.group(2)})"))
    sdk = re.search(r"(?m)^(?:min)?[sS]dkVersion:'(\d+)'", out)
    tgt = re.search(r"(?m)^targetSdkVersion:'(\d+)'", out)
    check(bool(sdk) and int(sdk.group(1)) == MIN_SDK, "minSdk", f"{sdk.group(1) if sdk else '?'} (ожидается {MIN_SDK})")
    check(bool(tgt) and int(tgt.group(1)) == TARGET_SDK, "targetSdk", f"{tgt.group(1) if tgt else '?'} (ожидается {TARGET_SDK})")
    check("application-icon-" in out, "Иконка есть в APK")
    check("launchable-activity" in out, "Есть запускаемая Activity")
    abis = re.search(r"native-code: (.*)", out)
    results.append(("INFO", f"Архитектуры: {abis.group(1) if abis else 'нет'}"))


# ---------- подпись ----------
def sha256_of_keystore(path, alias, password):
    out = run(["keytool", "-list", "-v", "-keystore", path, "-storepass", password, "-alias", alias])
    m = re.search(r"SHA256:\s*([0-9A-Fa-f:]+)", out.stdout)
    return m.group(1).replace(":", "").lower() if m else None


def audit_signature(apksigner, apk, signer_file):
    out = run([apksigner, "verify", "--verbose", "--print-certs", apk])
    ok = out.returncode == 0 and "Verifies" in out.stdout
    check(ok, "Подпись APK проверена apksigner", (out.stderr or "")[:200] if not ok else "")
    schemes = re.findall(r"Verified using (v\d(?:\.\d)?) scheme[^:]*: (true|false)", out.stdout)
    on = [s for s, v in schemes if v == "true"]
    check("v2" in on or "v3" in on, "Подпись схемы v2/v3 (нужна Android 7+)", ", ".join(on) or "нет")
    m = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-f]+)", out.stdout)
    digest = m.group(1) if m else None
    proto = sha256_of_keystore("signing/prototype.keystore", "codeacademy-proto", "android") if os.path.isfile("signing/prototype.keystore") else None
    kind = "prototype" if digest and proto and digest == proto else "release"
    results.append(("INFO", f"Подпись: SHA-256 {digest or '?'} — {'ключ ПРОТОТИПА (публичный, пароль «android»)' if kind == 'prototype' else 'релизный ключ'}"))
    check(kind == "release", "APK подписан релизным ключом, а не публичным ключом прототипа", warn_only=True)
    if signer_file:
        with open(signer_file, "w") as f:
            f.write(kind + "\n")


# ---------- содержимое ----------
def elf_align(data):
    """Минимальное выравнивание PT_LOAD сегментов ELF64 (16384 и больше — готово к страницам 16 КБ)."""
    if data[:4] != b"\x7fELF" or data[4] != 2:
        return None
    e_phoff = struct.unpack_from("<Q", data, 0x20)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x36)
    aligns = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", data, off)[0]
        if p_type == 1:
            aligns.append(struct.unpack_from("<Q", data, off + 48)[0])
    return min(aligns) if aligns else None


def group_of(name):
    if name.startswith("lib/"):
        return "lib/" + name.split("/")[1]
    if name.startswith("assets/"):
        parts = name.split("/")
        return "assets/" + (parts[1] if len(parts) > 2 else "")
    if name.endswith(".dex"):
        return "classes*.dex"
    return name.split("/")[0] if "/" in name else name


def audit_content(apk):
    z = zipfile.ZipFile(apk)
    groups, entries = {}, []
    for i in z.infolist():
        g = groups.setdefault(group_of(i.filename), [0, 0])
        g[0] += i.compress_size
        g[1] += i.file_size
        entries.append((i.compress_size, i.file_size, i.filename))
    total = os.path.getsize(apk)
    results.append(("INFO", f"Размер APK: {total / 1048576:.1f} МБ"))
    lines = ["| Часть | В APK, МБ | Распакованно, МБ |", "|---|---:|---:|"]
    for g, (c, u) in sorted(groups.items(), key=lambda kv: -kv[1][0])[:14]:
        lines.append(f"| {g} | {c / 1048576:.1f} | {u / 1048576:.1f} |")
    results.append(("TABLE", "\n".join(lines)))
    top = sorted(entries, reverse=True)[:8]
    results.append(("TABLE", "\n".join(["| Самые тяжёлые файлы | В APK, МБ |", "|---|---:|"] + [f"| {n} | {c / 1048576:.1f} |" for c, u, n in top])))
    names = {i.filename for i in z.infolist()}
    check("lib/arm64-v8a/libmentor.so" in names, "В APK есть libmentor.so для arm64 (телефон)")
    # Выравнивание .so под страницы 16 КБ (требование Google Play для targetSdk 35 на новых устройствах).
    bad, checked = [], 0
    for i in z.infolist():
        if i.filename.startswith("lib/arm64-v8a/") and i.filename.endswith(".so"):
            al = elf_align(z.read(i.filename))
            if al is not None:
                checked += 1
                if al < 16384:
                    bad.append(f"{os.path.basename(i.filename)}={al}")
    check(checked > 0 and not bad, "Нативные библиотеки arm64 выровнены под страницы 16 КБ",
          f"проверено {checked}; не выровнены: {', '.join(bad[:6]) or 'нет'}" + (f" (+{len(bad) - 6})" if len(bad) > 6 else ""), warn_only=True)
    stores = sorted(n for n in names if n.lower().endswith((".keystore", ".jks", ".p12", ".pfx")))
    private = []
    for i in z.infolist():
        if i.filename.lower().endswith((".pem", ".key")) and i.file_size < 4_000_000:
            if b"PRIVATE KEY" in z.read(i.filename):
                private.append(i.filename)
    pems = sorted(n for n in names if n.lower().endswith((".pem", ".key", ".crt")))
    if pems:
        results.append(("INFO", f"Файлы сертификатов в APK (публичные, закрытых ключей в них нет): {', '.join(pems[:6])}"))
    check(not stores and not private, "В APK нет хранилищ ключей и закрытых ключей", f"найдены: {stores + private}" if stores or private else "")
    check(not any(re.search(r"(^|/)(recordings?|voice_raw|raw_voice)/", n) for n in names), "В APK нет сырых записей голоса")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    apk = args[0]
    report = args[args.index("--report") + 1] if "--report" in args else None
    signer_file = args[args.index("--signer-file") + 1] if "--signer-file" in args else None
    aapt2, apksigner = find_tool("aapt2"), find_tool("apksigner")
    audit_badging(aapt2, apk)
    audit_manifest(aapt2, apk)
    audit_signature(apksigner, apk, signer_file)
    audit_content(apk)
    fails = [t for s, t in results if s == "FAIL"]
    warns = [t for s, t in results if s == "WARN"]
    md = [f"### Аудит APK: {'НАРУШЕНИЯ' if fails else 'нарушений нет'} (FAIL {len(fails)}, WARN {len(warns)})", ""]
    for s, t in results:
        if s in ("PASS", "FAIL", "WARN"):
            md.append(f"- {'✅' if s == 'PASS' else '❌' if s == 'FAIL' else '⚠️'} {t}")
        elif s == "INFO":
            md.append(f"- ℹ️ {t}")
        else:
            md += ["", t, ""]
    text = "\n".join(md)
    print(text)
    if report:
        with open(report, "w") as f:
            f.write(text + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
