#!/usr/bin/env bash
# ForgeFlow User-Level Distribution Installer
# Sets up ~/.local/share/forgeflow with versioned packages, atomic current symlink, and entrypoints in ~/.local/bin.

set -euo pipefail

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine script & repository directory (supports both local and remote curl execution)
TEMP_DIR=""
cleanup_temp() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup_temp EXIT

REPO_ROOT=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  CANDIDATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  if [ -f "$CANDIDATE_DIR/src/forgeflow/_version.py" ]; then
    REPO_ROOT="$CANDIDATE_DIR"
  fi
fi

if [ -z "$REPO_ROOT" ]; then
  TEMP_DIR="$(mktemp -d)"
  FORGEFLOW_REPO="${FORGEFLOW_REPO:-https://github.com/deepblue-kblee/forgeflow}"
  echo "Downloading ForgeFlow distribution package from $FORGEFLOW_REPO..."
  if command -v git >/dev/null 2>&1; then
    git clone --depth 1 "$FORGEFLOW_REPO" "$TEMP_DIR/forgeflow" >/dev/null 2>&1 || {
      curl -sSL "${FORGEFLOW_REPO}/archive/refs/heads/main.tar.gz" | tar -xz -C "$TEMP_DIR"
      mv "$TEMP_DIR"/forgeflow-* "$TEMP_DIR/forgeflow"
    }
  else
    curl -sSL "${FORGEFLOW_REPO}/archive/refs/heads/main.tar.gz" | tar -xz -C "$TEMP_DIR"
    mv "$TEMP_DIR"/forgeflow-* "$TEMP_DIR/forgeflow"
  fi
  REPO_ROOT="$TEMP_DIR/forgeflow"
fi

# Defaults: OS user account-level installation (matches agent skills lifecycle)
DEFAULT_PREFIX="${HOME}/.local/share/forgeflow"
DEFAULT_BIN_DIR="${HOME}/.local/bin"
PREFIX="${FORGEFLOW_INSTALL_DIR:-$DEFAULT_PREFIX}"
BIN_DIR="${FORGEFLOW_BIN_DIR:-$DEFAULT_BIN_DIR}"
FORCE=false
DRY_RUN=false
KEEP_COUNT=5
ROLLBACK_VERSION=""

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_dryrun() {
  echo -e "${CYAN}[DRY-RUN]${NC} $1"
}

usage() {
  cat << USAGE
Usage: $0 [OPTIONS]

ForgeFlow User-Level Distribution Installer
Installs ForgeFlow for the current OS user account into ~/.local/share/forgeflow and ~/.local/bin.

Options:
  --prefix <path>        Installation root directory (default: ~/.local/share/forgeflow)
  --bin-dir <path>       CLI executable symlink directory (default: ~/.local/bin)
  --force                Refresh installation of the same content-addressed build
  --keep <N>             Number of latest packages to keep (default: 5)
  --rollback <version>   Switch active version to a previously installed version
  --dry-run              Simulate installation actions without modifying filesystem
  -h, --help             Show this help message

Examples:
  $0                     Install for current user into ~/.local/share/forgeflow and ~/.local/bin
  $0 --dry-run           Preview installation actions
  $0 --rollback 0.22.1   Rollback current version to 0.22.1
USAGE
  exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      PREFIX="$2"
      shift 2
      ;;
    --bin-dir)
      BIN_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --keep)
      KEEP_COUNT="$2"
      shift 2
      ;;
    --rollback)
      ROLLBACK_VERSION="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      log_error "Unknown option: $1"
      usage
      ;;
  esac
done

cmd_run() {
  if [ "$DRY_RUN" = true ]; then
    log_dryrun "$*"
    return 0
  fi
  "$@"
}

generate_package_skills() (
  local generator="$1"
  local external_skills="${2:-0}"
  local skills_target="${FORGEFLOW_SKILLS_DIR:-${HOME}/.agents/skills}"
  local skills_stage=""
  local skills_transaction=""
  local published_skills=""
  local created_skill_dirs=""
  local publication_complete=false
  local skill_name=""

  cleanup_skill_publication() {
    local name=""
    if [ "$publication_complete" = false ] && [ -n "$skills_transaction" ]; then
      for name in $published_skills; do
        if [ -f "$skills_transaction/old/$name" ]; then
          mv -f "$skills_transaction/old/$name" "$skills_target/$name/SKILL.md" || {
            log_error "Could not restore $skills_target/$name/SKILL.md; recover it from $skills_transaction/old/$name."
            return 1
          }
        else
          rm -f "$skills_target/$name/SKILL.md" || return 1
        fi
      done
      for name in $created_skill_dirs; do
        rmdir "$skills_target/$name" 2>/dev/null || true
      done
    fi
    [ -z "$skills_stage" ] || rm -rf "$skills_stage"
    [ -z "$skills_transaction" ] || rm -rf "$skills_transaction"
  }
  trap cleanup_skill_publication EXIT
  trap 'exit 1' HUP INT TERM
  if [ "$DRY_RUN" = true ]; then
    log_dryrun "Generate skills from $generator into $skills_target before activation"
    return 0
  fi
  if [ ! -f "$generator" ] || [ -L "$generator" ]; then
    log_error "Selected package has no restorable skill generator. Keep the current build active; reinstall the desired complete distribution explicitly."
    return 1
  fi
  skills_stage="$(mktemp -d)" || return 1
  if ! FORGEFLOW_SKILLS_DIR="$skills_stage" FORGEFLOW_INSTALL_SPECKIT_SKILLS="$external_skills" bash "$generator"; then
    rm -rf "$skills_stage"
    log_error "Selected package skill generation failed; current build was not changed."
    return 1
  fi
  for skill_name in setup-forgeflow update-forgeflow forgeflow forgeflow-graphify; do
    if [ ! -f "$skills_stage/$skill_name/SKILL.md" ] || [ -L "$skills_stage/$skill_name/SKILL.md" ]; then
      rm -rf "$skills_stage"
      log_error "Selected package did not generate all required skills; current build was not changed."
      return 1
    fi
  done
  # Check every destination before changing even the first installed skill.
  # Symlinks are rejected so publication and recovery stay inside this tree.
  if [ -L "$skills_target" ] || { [ -e "$skills_target" ] && [ ! -d "$skills_target" ]; }; then
    log_error "Skills destination must be a directory without a symlink: $skills_target"
    return 1
  fi
  for skill_name in setup-forgeflow update-forgeflow forgeflow forgeflow-graphify; do
    if [ -L "$skills_target/$skill_name" ] || { [ -e "$skills_target/$skill_name" ] && [ ! -d "$skills_target/$skill_name" ]; } ||
       [ -L "$skills_target/$skill_name/SKILL.md" ] || { [ -e "$skills_target/$skill_name/SKILL.md" ] && [ ! -f "$skills_target/$skill_name/SKILL.md" ]; }; then
      log_error "Invalid skill destination: $skills_target/$skill_name; current build and skills were not changed."
      return 1
    fi
  done
  mkdir -p "$skills_target" || return 1
  skills_transaction="$(mktemp -d "$skills_target/.forgeflow-skills.XXXXXX")" || return 1
  mkdir "$skills_transaction/old" "$skills_transaction/new" || return 1
  for skill_name in setup-forgeflow update-forgeflow forgeflow forgeflow-graphify; do
    cp "$skills_stage/$skill_name/SKILL.md" "$skills_transaction/new/$skill_name" || return 1
    if [ -f "$skills_target/$skill_name/SKILL.md" ]; then
      cp -p "$skills_target/$skill_name/SKILL.md" "$skills_transaction/old/$skill_name" || return 1
    fi
  done
  for skill_name in setup-forgeflow update-forgeflow forgeflow forgeflow-graphify; do
    if [ ! -d "$skills_target/$skill_name" ]; then
      created_skill_dirs="$created_skill_dirs $skill_name"
      mkdir "$skills_target/$skill_name" || return 1
    fi
    published_skills="$skill_name $published_skills"
    if ! mv -f "$skills_transaction/new/$skill_name" "$skills_target/$skill_name/SKILL.md"; then
      log_error "Could not publish generated skills; restoring the previous skills and keeping the current build."
      return 1
    fi
  done
  publication_complete=true
)

# Handle Rollback if requested
if [ -n "$ROLLBACK_VERSION" ]; then
  if [[ ! "$ROLLBACK_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-f0-9]+)?$ ]]; then
    log_error "Rollback must name an installed version or version-content identity."
    exit 1
  fi
  log_info "Initiating rollback to version $ROLLBACK_VERSION..."
  TARGET_PKG_DIR="$PREFIX/packages/$ROLLBACK_VERSION"
  if [ ! -d "$TARGET_PKG_DIR" ]; then
    log_error "Target package version directory does not exist: $TARGET_PKG_DIR"
    exit 1
  fi

  # Restore the generator belonging to this build, never the current checkout's
  # newer instructions. Legacy packages without it cannot be safely activated.
  generate_package_skills "$TARGET_PKG_DIR/scripts/install-skills.sh" 0 || exit 1

  cmd_run ln -sfn "packages/$ROLLBACK_VERSION" "$PREFIX/current"
  cmd_run ln -sfn "../current/bin/forgeflow" "$PREFIX/bin/forgeflow"
  cmd_run ln -sfn "../current/bin/harness" "$PREFIX/bin/harness"

  cmd_run mkdir -p "$BIN_DIR"
  cmd_run ln -sfn "$PREFIX/bin/forgeflow" "$BIN_DIR/forgeflow"
  cmd_run ln -sfn "$PREFIX/bin/harness" "$BIN_DIR/harness"

  log_info "Successfully rolled back active version to $ROLLBACK_VERSION."
  exit 0
fi

# Detect version from canonical source
VERSION_FILE="$REPO_ROOT/src/forgeflow/_version.py"
if [ ! -f "$VERSION_FILE" ]; then
  log_error "Cannot find version file at $VERSION_FILE"
  exit 1
fi

VERSION=$(grep -E '^__version__\s*=' "$VERSION_FILE" | sed -E 's/.*["'"'"']([^"'"'"']+)["'"'"'].*/\1/')
if [ -z "$VERSION" ]; then
  log_error "Failed to extract version from $VERSION_FILE"
  exit 1
fi

log_info "ForgeFlow framework version: $VERSION"

# Validate Python interpreter (Python >= 3.10)
PYTHON_CANDIDATE=""
for candidate in "${FORGEFLOW_PYTHON:-}" /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
  if [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
      PYTHON_CANDIDATE="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON_CANDIDATE" ]; then
  log_error "Python 3.10 or higher is required but was not found in standard paths."
  exit 1
fi

PYTHON_VERSION=$("$PYTHON_CANDIDATE" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
log_info "Using Python interpreter: $PYTHON_CANDIDATE ($PYTHON_VERSION)"

# Content identity includes runtime, specifications, templates and skill generation.
# Different builds of the same version never overwrite one another.
BUILD_ID=$("$PYTHON_CANDIDATE" - "$REPO_ROOT" <<'PY'
import hashlib
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
paths = [p for p in (root / 'src/forgeflow').rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
paths += [root / 'install.sh', root / 'scripts/install-skills.sh']
result = hashlib.sha256()
for path in sorted(paths):
    name = path.relative_to(root).as_posix().encode()
    data = path.read_bytes()
    result.update(len(name).to_bytes(8, 'big') + name)
    result.update(len(data).to_bytes(8, 'big') + data)
print(result.hexdigest())
PY
)
PACKAGE_KEY="${VERSION}-${BUILD_ID:0:16}"

# Package target directories
PKG_DIR="$PREFIX/packages/$PACKAGE_KEY"
PKG_LIB_DIR="$PKG_DIR/lib/forgeflow"
PKG_BIN_DIR="$PKG_DIR/bin"

# Detect existing active installation
CURRENT_ACTIVE=""
if [ -L "$PREFIX/current" ]; then
  CURRENT_ACTIVE=$(basename "$(readlink "$PREFIX/current" 2>/dev/null || echo "")")
fi

if [ -n "$CURRENT_ACTIVE" ]; then
  log_info "Detected existing active installation: $CURRENT_ACTIVE"
fi

if [ -d "$PKG_DIR" ] && [ "$FORCE" = false ]; then
  log_info "Package version $VERSION already exists at $PKG_DIR. Synchronizing files to latest build..."
fi

log_info "Installing ForgeFlow $VERSION into $PREFIX..."

# 1. Create directory hierarchy
cmd_run mkdir -p "$PREFIX/packages"
cmd_run mkdir -p "$PREFIX/bin"
cmd_run chmod 755 "$PREFIX"
cmd_run chmod 755 "$PREFIX/packages"
cmd_run chmod 755 "$PREFIX/bin"

cmd_run mkdir -p "$PKG_LIB_DIR"
cmd_run mkdir -p "$PKG_BIN_DIR"
cmd_run mkdir -p "$PKG_DIR/scripts"
if [ ! -f "$REPO_ROOT/scripts/install-skills.sh" ]; then
  log_error "Distribution is incomplete: scripts/install-skills.sh is missing."
  exit 1
fi
cmd_run cp "$REPO_ROOT/scripts/install-skills.sh" "$PKG_DIR/scripts/install-skills.sh"

# 2. Copy source modules and resources
log_info "Copying forgeflow library files..."
SRC_DIR="$REPO_ROOT/src/forgeflow"

for py_file in "$SRC_DIR"/*.py; do
  if [ -f "$py_file" ]; then
    cmd_run cp "$py_file" "$PKG_LIB_DIR/"
  fi
done

if [ -d "$SRC_DIR/templates" ]; then
  cmd_run cp -R "$SRC_DIR/templates" "$PKG_LIB_DIR/"
  # Purge legacy templates from new package
  if [ "$DRY_RUN" = false ]; then
    for legacy_tmpl in PRD.md DESIGN.md ROADMAP.md GOVERNANCE.md RELEASE_NOTES.md; do
      rm -f "$PKG_LIB_DIR/templates/$legacy_tmpl"
    done
  fi
fi

if [ -d "$SRC_DIR/spec" ]; then
  log_info "Copying official specification files and router..."
  cmd_run cp -R "$SRC_DIR/spec" "$PKG_LIB_DIR/"
fi

if [ -d "$SRC_DIR/adr" ]; then
  cmd_run cp -R "$SRC_DIR/adr" "$PKG_LIB_DIR/"
fi

# Keep history in the package snapshot and the compatibility prefix location.
if [ -f "$REPO_ROOT/src/forgeflow/CHANGELOG.md" ]; then
  cmd_run cp "$REPO_ROOT/src/forgeflow/CHANGELOG.md" "$PKG_LIB_DIR/CHANGELOG.md"
  cmd_run cp "$REPO_ROOT/src/forgeflow/CHANGELOG.md" "$PREFIX/CHANGELOG.md"
  cmd_run chmod 644 "$PREFIX/CHANGELOG.md"
elif [ -f "$REPO_ROOT/docs/CHANGELOG.md" ]; then
  cmd_run cp "$REPO_ROOT/docs/CHANGELOG.md" "$PKG_LIB_DIR/CHANGELOG.md"
  cmd_run cp "$REPO_ROOT/docs/CHANGELOG.md" "$PREFIX/CHANGELOG.md"
  cmd_run chmod 644 "$PREFIX/CHANGELOG.md"
fi

if [ -d "$SRC_DIR/catalog_oracles" ]; then
  cmd_run cp -R "$SRC_DIR/catalog_oracles" "$PKG_LIB_DIR/"
fi

# Clean up any copied __pycache__
if [ "$DRY_RUN" = false ]; then
  find "$PKG_LIB_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find "$PKG_LIB_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
  cmd_run chmod -R 755 "$PKG_DIR"
  cmd_run find "$PKG_LIB_DIR" -type f -exec chmod 644 {} +
fi

# 3. Write package metadata
GIT_COMMIT=""
if command -v git >/dev/null 2>&1 && [ -d "$REPO_ROOT/.git" ]; then
  GIT_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%d")

METADATA_FILE="$PKG_DIR/package.json"
if [ "$DRY_RUN" = true ]; then
  log_dryrun "Write package metadata to $METADATA_FILE"
else
  cat << EOF > "$METADATA_FILE"
{
  "name": "forgeflow",
  "version": "$VERSION",
  "content_identity": "$BUILD_ID",
  "installed_at": "$TIMESTAMP",
  "git_commit": "$GIT_COMMIT",
  "installed_by": "$USER",
  "python_version": "$PYTHON_VERSION",
  "python_interpreter": "$PYTHON_CANDIDATE"
}
EOF
  chmod 644 "$METADATA_FILE"
fi

# 4. Generate standalone launcher script
LAUNCHER_FILE="$PKG_BIN_DIR/forgeflow"
log_info "Generating standalone launcher: $LAUNCHER_FILE..."
if [ "$DRY_RUN" = true ]; then
  log_dryrun "Write executable launcher to $LAUNCHER_FILE"
else
  cat << 'EOF' > "$LAUNCHER_FILE"
#!/usr/bin/env bash
set -euo pipefail

# Dynamic resolution of canonical package lib directory across symlinks
SOURCE="${BASH_SOURCE[0]:-$0}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
BIN_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
PKG_DIR="$(cd -P "$BIN_DIR/.." >/dev/null 2>&1 && pwd)"
export PYTHONPATH="$PKG_DIR/lib:${PYTHONPATH:-}"

PYTHON_BIN="${FORGEFLOW_PYTHON:-}"
if [ -z "$PYTHON_BIN" ]; then
  for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        PYTHON_BIN="$candidate"
        break
      fi
    fi
  done
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "Error: Python 3.10 or higher is required to run ForgeFlow." >&2
  exit 1
fi

exec "$PYTHON_BIN" -m forgeflow.cli "$@"
EOF
  chmod 755 "$LAUNCHER_FILE"
  ln -sfn "forgeflow" "$PKG_BIN_DIR/harness"
fi

# 5. Generate instructions from this exact package before changing current.
generate_package_skills "$PKG_DIR/scripts/install-skills.sh" "${FORGEFLOW_INSTALL_SPECKIT_SKILLS:-0}" || exit 1

# Activate the selected CLI/spec/skill distribution.
log_info "Switching active build symlink (current -> packages/$PACKAGE_KEY)..."
cmd_run ln -sfn "packages/$PACKAGE_KEY" "$PREFIX/current"
cmd_run ln -sfn "../current/bin/forgeflow" "$PREFIX/bin/forgeflow"
cmd_run ln -sfn "../current/bin/harness" "$PREFIX/bin/harness"

# 6. Global entrypoints in user BIN_DIR (~/.local/bin)
cmd_run mkdir -p "$BIN_DIR"
log_info "Linking CLI commands in $BIN_DIR..."
cmd_run ln -sfn "$PREFIX/bin/forgeflow" "$BIN_DIR/forgeflow"
cmd_run ln -sfn "$PREFIX/bin/harness" "$BIN_DIR/harness"

# 7. Retention cleanup
if [ "$KEEP_COUNT" -gt 0 ] && [ "$DRY_RUN" = false ]; then
  log_info "Applying package retention policy (keeping latest $KEEP_COUNT packages)..."
  INSTALLED_PKGS=$(find "$PREFIX/packages" -mindepth 1 -maxdepth 1 -type d | sort -V)
  TOTAL_COUNT=$(echo "$INSTALLED_PKGS" | grep -v '^$' | wc -l | tr -d ' ')
  if [ "$TOTAL_COUNT" -gt "$KEEP_COUNT" ]; then
    REMOVE_COUNT=$((TOTAL_COUNT - KEEP_COUNT))
    echo "$INSTALLED_PKGS" | head -n "$REMOVE_COUNT" | while read -r old_pkg; do
      if [ -d "$old_pkg" ] && [ "$(basename "$old_pkg")" != "$PACKAGE_KEY" ]; then
        log_info "Pruning old package version: $(basename "$old_pkg")"
        rm -rf "$old_pkg"
      fi
    done
  fi
fi

# 8. Post-installation verification
log_info "Verifying installation..."
if [ "$DRY_RUN" = false ]; then
  if [ -x "$BIN_DIR/forgeflow" ]; then
    if ! INSTALLED_VER=$("$BIN_DIR/forgeflow" version 2>/dev/null); then
      log_error "Installed entrypoint failed its version probe."
      exit 1
    fi
    if [[ "$INSTALLED_VER" != *"v$VERSION"* ]]; then
      log_error "Installed entrypoint version does not match the selected build."
      exit 1
    fi
    if ! "$BIN_DIR/forgeflow" workflow --help >/dev/null; then
      log_error "Installed workflow entrypoint failed its delivery probe."
      exit 1
    fi
    log_info "Verified: $INSTALLED_VER"
  else
    log_error "$BIN_DIR/forgeflow was not found or is not executable."
    exit 1
  fi
fi

# 10. Check if BIN_DIR is in PATH
if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
  log_warn "$BIN_DIR is not currently in your PATH."
  log_warn "Add the following line to your ~/.zshrc or ~/.bashrc to use 'forgeflow':"
  log_warn "  export PATH=\"$BIN_DIR:\$PATH\""
fi

log_info "ForgeFlow $VERSION successfully installed for user $(whoami)."
log_info "Location: $PREFIX (CLI binaries in $BIN_DIR)"
log_info "Active build: $PREFIX/current ($BUILD_ID). Existing project snapshots retain their baseline."
log_info "Agent skills (setup-forgeflow, update-forgeflow) configured in ~/.agents/skills/."
