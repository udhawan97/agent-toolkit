#!/bin/zsh
set -eu

apply_changes=0
canonical_app=""
primary_bundle_id=""
receipt_path=""
script_name="${0:t}"
typeset -a legacy_bundle_ids legacy_executables supplied_scan_roots

usage() {
  print "Usage: ${script_name} --canonical-app PATH --bundle-id ID [options]"
  print ""
  print "Options:"
  print "  --legacy-bundle-id ID  Include a proven former bundle identifier (repeatable)."
  print "  --legacy-executable NAME Include a proven former executable name (repeatable)."
  print "  --scan-root PATH        Scan an additional project/build root (repeatable)."
  print "  --receipt PATH          Write or verify an owner-only preview receipt."
  print "  --apply                 Move only candidates bound to --receipt."
  print "  -h, --help              Show this help."
}

require_value() {
  if (( $# < 2 )) || [[ -z "${2}" ]]; then
    print -u2 "Missing value for ${1}."
    usage >&2
    exit 2
  fi
}

while (( $# > 0 )); do
  case "${1}" in
    --canonical-app)
      require_value "${1}" "${2:-}"
      canonical_app="${2}"
      shift 2
      ;;
    --bundle-id)
      require_value "${1}" "${2:-}"
      primary_bundle_id="${2}"
      shift 2
      ;;
    --legacy-bundle-id)
      require_value "${1}" "${2:-}"
      legacy_bundle_ids+=("${2}")
      shift 2
      ;;
    --legacy-executable)
      require_value "${1}" "${2:-}"
      if [[ "${2}" == */* ]]; then
        print -u2 "Legacy executable names must not contain '/': ${2}"
        exit 2
      fi
      legacy_executables+=("${2}")
      shift 2
      ;;
    --scan-root)
      require_value "${1}" "${2:-}"
      supplied_scan_roots+=("${2}")
      shift 2
      ;;
    --receipt)
      require_value "${1}" "${2:-}"
      receipt_path="${2}"
      shift 2
      ;;
    --apply)
      apply_changes=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      print -u2 "Unknown option: ${1}"
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${canonical_app}" || -z "${primary_bundle_id}" ]]; then
  print -u2 "Both --canonical-app and --bundle-id are required."
  usage >&2
  exit 2
fi

if [[ -n "${receipt_path}" && "${receipt_path}" != /* ]]; then
  print -u2 -- "--receipt must be an absolute path."
  exit 2
fi
if (( apply_changes != 0 )) && [[ -z "${receipt_path}" ]]; then
  print -u2 -- "--apply requires the owner-only receipt created by the approved preview."
  exit 2
fi

user_home="${HOME:?HOME is not set}"
if [[ "${canonical_app}" == '~/'* ]]; then
  canonical_app="${user_home}/${canonical_app#\~/}"
fi
if [[ "${canonical_app}" != /* ]]; then
  print -u2 -- "--canonical-app must be an absolute path."
  exit 2
fi

typeset -a allowed_bundle_ids normalized_bundle_ids scan_roots
allowed_bundle_ids=("${primary_bundle_id}" "${legacy_bundle_ids[@]}")
for bundle_id in "${allowed_bundle_ids[@]}"; do
  if [[ ! "${bundle_id}" =~ '^[A-Za-z0-9][A-Za-z0-9._-]*$' ]]; then
    print -u2 "Invalid bundle identifier: ${bundle_id}"
    exit 2
  fi
  normalized_bundle_ids+=("${bundle_id:l}")
done

trash_root="${user_home}/.Trash"
launch_services="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
scan_roots=(
  "/Applications"
  "${user_home}/Applications"
  "${user_home}/Library/Developer/Xcode/DerivedData"
  "${supplied_scan_roots[@]}"
)

spotlight_query="kMDItemContentType == 'com.apple.application-bundle' && ("
separator=""
for bundle_id in "${allowed_bundle_ids[@]}"; do
  spotlight_query+="${separator}kMDItemCFBundleIdentifier == '${bundle_id}'"
  separator=" || "
done
spotlight_query+=")"

bundle_identifier() {
  [[ -f "$1/Contents/Info.plist" ]] || return 0
  /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$1/Contents/Info.plist" 2>/dev/null || true
}

bundle_executable() {
  [[ -f "$1/Contents/Info.plist" ]] || return 0
  /usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$1/Contents/Info.plist" 2>/dev/null || true
}

signing_team() {
  command -v codesign >/dev/null 2>&1 || return 0
  codesign -dv --verbose=4 "$1" 2>&1 | /usr/bin/sed -n 's/^TeamIdentifier=//p' || true
}

file_sha256() {
  [[ -f "$1" ]] || {
    print "missing"
    return 0
  }
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}

value_is_receipt_safe() {
  [[ "$1" != *$'\n'* && "$1" != *$'\t'* && "$1" != *$'\r'* ]]
}

path_is_approved() {
  local app_path="${1:A}" scan_root normalized_root
  for scan_root in "${scan_roots[@]}"; do
    [[ -n "${scan_root}" ]] || continue
    if [[ "${scan_root}" == '~/'* ]]; then
      scan_root="${user_home}/${scan_root#\~/}"
    fi
    normalized_root="${scan_root:A}"
    [[ "${app_path}" == "${normalized_root}" || "${app_path}" == "${normalized_root}"/* ]] && return 0
  done
  return 1
}

bundle_id_is_allowed() {
  local candidate_id="${1:l}" allowed_id
  for allowed_id in "${normalized_bundle_ids[@]}"; do
    [[ "${candidate_id}" == "${allowed_id}" ]] && return 0
  done
  return 1
}

canonical_id="$(bundle_identifier "${canonical_app}")"
if [[ ! -d "${canonical_app}" ]]; then
  print -u2 "Canonical app is missing at ${canonical_app}."
  exit 1
fi
if [[ "${canonical_id:l}" != "${primary_bundle_id:l}" ]]; then
  print -u2 "Canonical app has bundle identifier '${canonical_id}', expected '${primary_bundle_id}'."
  exit 1
fi
canonical_executable="$(bundle_executable "${canonical_app}")"
if [[ -z "${canonical_executable}" ]]; then
  print -u2 "Canonical app has no CFBundleExecutable value."
  exit 1
fi
if [[ ! -f "${canonical_app}/Contents/MacOS/${canonical_executable}" ]]; then
  print -u2 "Canonical app executable is missing: ${canonical_executable}"
  exit 1
fi
canonical_team="$(signing_team "${canonical_app}")"
typeset -a allowed_executables
allowed_executables=("${canonical_executable}" "${legacy_executables[@]}")

executable_is_allowed() {
  local candidate_executable="$1" allowed_executable
  for allowed_executable in "${allowed_executables[@]}"; do
    [[ "${candidate_executable}" == "${allowed_executable}" ]] && return 0
  done
  return 1
}

typeset -a discovered_paths candidate_paths outside_scan_paths identity_mismatch_paths
typeset -A seen_paths

add_discovered_path() {
  local app_path="$1"
  [[ -d "${app_path}" && "${app_path}" == *.app ]] || return 0
  [[ -z "${seen_paths[${app_path}]:-}" ]] || return 0
  seen_paths[${app_path}]=1
  discovered_paths+=("${app_path}")
}

discover_apps() {
  local app_path scan_root app_id app_executable app_team
  discovered_paths=()
  candidate_paths=()
  outside_scan_paths=()
  identity_mismatch_paths=()
  seen_paths=()

  while IFS= read -r app_path; do
    add_discovered_path "${app_path}"
  done < <(mdfind "${spotlight_query}" 2>/dev/null || true)

  for scan_root in "${scan_roots[@]}"; do
    if [[ "${scan_root}" == '~/'* ]]; then
      scan_root="${user_home}/${scan_root#\~/}"
    fi
    [[ -d "${scan_root}" ]] || continue
    while IFS= read -r app_path; do
      add_discovered_path "${app_path}"
    done < <(/usr/bin/find "${scan_root}" -type d -name '*.app' -prune -print 2>/dev/null)
  done

  for app_path in "${discovered_paths[@]}"; do
    [[ "${app_path:A}" != "${canonical_app:A}" ]] || continue
    [[ "${app_path}" != /Volumes/* && "${app_path}" != "${trash_root}"/* ]] || continue
    app_id="$(bundle_identifier "${app_path}")"
    bundle_id_is_allowed "${app_id}" || continue
    app_executable="$(bundle_executable "${app_path}")"
    if ! executable_is_allowed "${app_executable}" || [[ ! -f "${app_path}/Contents/MacOS/${app_executable}" ]]; then
      identity_mismatch_paths+=("${app_path}")
      continue
    fi
    if [[ -n "${canonical_team}" && "${canonical_team}" != "not set" ]]; then
      app_team="$(signing_team "${app_path}")"
      if [[ "${app_team}" != "${canonical_team}" ]]; then
        identity_mismatch_paths+=("${app_path}")
        continue
      fi
    fi
    if path_is_approved "${app_path}"; then
      candidate_paths+=("${app_path}")
    else
      outside_scan_paths+=("${app_path}")
    fi
  done
}

discover_apps

candidate_paths=("${(@on)candidate_paths}")

emit_receipt() {
  local app_path app_id app_executable app_team info_sha executable_sha
  value_is_receipt_safe "${canonical_app:A}" || return 1
  value_is_receipt_safe "${canonical_id}" || return 1
  value_is_receipt_safe "${canonical_executable}" || return 1
  value_is_receipt_safe "${canonical_team}" || return 1
  info_sha="$(file_sha256 "${canonical_app}/Contents/Info.plist")"
  executable_sha="$(file_sha256 "${canonical_app}/Contents/MacOS/${canonical_executable}")"
  print -r -- "agent-toolkit-cleanup-receipt-v1"
  print -r -- "canonical"$'\t'"${canonical_app:A}"$'\t'"${canonical_id}"$'\t'"${canonical_executable}"$'\t'"${canonical_team}"$'\t'"${info_sha}"$'\t'"${executable_sha}"
  for app_path in "${candidate_paths[@]}"; do
    app_id="$(bundle_identifier "${app_path}")"
    app_executable="$(bundle_executable "${app_path}")"
    app_team="$(signing_team "${app_path}")"
    value_is_receipt_safe "${app_path:A}" || return 1
    value_is_receipt_safe "${app_id}" || return 1
    value_is_receipt_safe "${app_executable}" || return 1
    value_is_receipt_safe "${app_team}" || return 1
    info_sha="$(file_sha256 "${app_path}/Contents/Info.plist")"
    executable_sha="$(file_sha256 "${app_path}/Contents/MacOS/${app_executable}")"
    print -r -- "candidate"$'\t'"${app_path:A}"$'\t'"${app_id}"$'\t'"${app_executable}"$'\t'"${app_team}"$'\t'"${info_sha}"$'\t'"${executable_sha}"
  done
}

write_preview_receipt() {
  local receipt_parent receipt_temporary
  receipt_parent="${receipt_path:h}"
  if [[ ! -d "${receipt_parent}" || -L "${receipt_parent}" ]]; then
    print -u2 "Receipt parent must be an existing, non-symlink directory: ${receipt_parent}"
    return 1
  fi
  if [[ -e "${receipt_path}" || -L "${receipt_path}" ]]; then
    print -u2 "Refusing to overwrite an existing receipt path: ${receipt_path}"
    return 1
  fi
  umask 077
  receipt_temporary="$(/usr/bin/mktemp "${receipt_parent}/.${receipt_path:t}.tmp.XXXXXX")"
  if ! emit_receipt > "${receipt_temporary}"; then
    /bin/rm -f -- "${receipt_temporary}"
    print -u2 "A receipt value contains a tab, newline, or carriage return."
    return 1
  fi
  /bin/chmod 600 "${receipt_temporary}"
  /bin/mv "${receipt_temporary}" "${receipt_path}"
}

verify_preview_receipt() {
  local receipt_mode receipt_temporary
  if [[ ! -f "${receipt_path}" || -L "${receipt_path}" || ! -O "${receipt_path}" ]]; then
    print -u2 "Apply receipt must be an owner-controlled regular file: ${receipt_path}"
    return 1
  fi
  receipt_mode="$(/usr/bin/stat -f '%Lp' "${receipt_path}" 2>/dev/null || true)"
  if [[ "${receipt_mode}" != "600" ]]; then
    print -u2 "Apply receipt must have owner-only mode 600: ${receipt_path}"
    return 1
  fi
  umask 077
  receipt_temporary="$(/usr/bin/mktemp "${TMPDIR:-/tmp}/agent-toolkit-cleanup-current.XXXXXX")"
  if ! emit_receipt > "${receipt_temporary}"; then
    /bin/rm -f -- "${receipt_temporary}"
    print -u2 "A receipt value contains a tab, newline, or carriage return."
    return 1
  fi
  /bin/chmod 600 "${receipt_temporary}"
  if ! /usr/bin/cmp -s "${receipt_path}" "${receipt_temporary}"; then
    /bin/rm -f -- "${receipt_temporary}"
    print -u2 "Cleanup targets or identity fingerprints changed after preview; refusing to move anything."
    print -u2 "Run a new preview with a new receipt, review it, and approve that exact result."
    return 1
  fi
  /bin/rm -f -- "${receipt_temporary}"
}

print "Canonical app: ${canonical_app} (${canonical_id})"
if (( ${#candidate_paths[@]} == 0 )); then
  print "No stale matching app bundles found."
else
  print "Stale matching app bundles:"
  for app_path in "${candidate_paths[@]}"; do
    print "  ${app_path} ($(bundle_identifier "${app_path}"), $(bundle_executable "${app_path}"))"
  done
fi
if (( ${#outside_scan_paths[@]} != 0 )); then
  print "Matching apps outside approved cleanup roots (will not move):"
  for app_path in "${outside_scan_paths[@]}"; do
    print "  ${app_path}"
  done
  print "Re-run the preview with an explicit --scan-root only if these paths are expected project artifacts."
fi
if (( ${#identity_mismatch_paths[@]} != 0 )); then
  print "Same-ID apps with a different executable or signing team (will not move):"
  for app_path in "${identity_mismatch_paths[@]}"; do
    print "  ${app_path}"
  done
fi

if (( apply_changes == 0 )); then
  if [[ -n "${receipt_path}" ]]; then
    write_preview_receipt
    print "Preview receipt: ${receipt_path}"
    print "Preview only. After approving these exact targets, re-run with the same arguments and receipt plus --apply."
  else
    print "Preview only. Re-run with a new absolute --receipt path, review that preview, then use the same receipt with --apply."
  fi
  exit 0
fi

verify_preview_receipt

/bin/mkdir -p "${trash_root}"
timestamp="$(/bin/date '+%Y%m%d-%H%M%S')"
typeset -a failed_paths
integer index=0

for app_path in "${candidate_paths[@]}"; do
  [[ -d "${app_path}" ]] || continue
  (( index += 1 ))
  app_name="${app_path:t:r}"
  trash_path="${trash_root}/${app_name}-stale-${timestamp}-${index}.app"

  if [[ -x "${launch_services}" ]]; then
    "${launch_services}" -u "${app_path}" >/dev/null 2>&1 || true
  fi

  if /bin/mv "${app_path}" "${trash_path}"; then
    print "Moved to Trash: ${app_path} -> ${trash_path}"
  else
    print -u2 "Could not move: ${app_path}"
    failed_paths+=("${app_path}")
  fi
done

if [[ -x "${launch_services}" ]]; then
  "${launch_services}" -f "${canonical_app}" >/dev/null 2>&1 || true
fi
/usr/bin/mdimport "${canonical_app}" >/dev/null 2>&1 || true

discover_apps
if (( ${#candidate_paths[@]} != 0 )); then
  print -u2 "Cleanup incomplete. Matching app bundles still exist:"
  for app_path in "${candidate_paths[@]}"; do
    print -u2 "  ${app_path}"
  done
  exit 1
fi
if (( ${#failed_paths[@]} != 0 )); then
  print -u2 "Cleanup incomplete because one or more app bundles could not be moved."
  exit 1
fi

typeset -a indexed_stale_paths
integer canonical_is_indexed=0
while IFS= read -r app_path; do
  [[ -d "${app_path}" ]] || continue
  [[ "${app_path}" != /Volumes/* && "${app_path}" != "${trash_root}"/* ]] || continue
  app_id="$(bundle_identifier "${app_path}")"
  bundle_id_is_allowed "${app_id}" || continue
  if [[ "${app_path:A}" == "${canonical_app:A}" ]]; then
    canonical_is_indexed=1
  else
    indexed_stale_paths+=("${app_path}")
  fi
done < <(mdfind "${spotlight_query}" 2>/dev/null || true)

if (( canonical_is_indexed == 0 )); then
  print -u2 "Cleanup moved stale bundles, but Spotlight has not indexed ${canonical_app} yet."
  print -u2 "Re-run after metadata indexing catches up before claiming success."
  exit 1
fi
if (( ${#indexed_stale_paths[@]} != 0 )); then
  print -u2 "Spotlight still indexes matching live bundles:"
  for app_path in "${indexed_stale_paths[@]}"; do
    print -u2 "  ${app_path}"
  done
  exit 1
fi

print "Cleanup complete. Spotlight live match: ${canonical_app} (${canonical_id})"
print "Moved bundles remain recoverable in ${trash_root}."
