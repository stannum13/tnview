#!/usr/bin/env sh
set -eu

REPO_ROOT=$(git rev-parse --show-toplevel)
BASE_DIR=${1:-"$(dirname "$REPO_ROOT")"}
BASE_REF=${BASE_REF:-main}

create_worktree() {
	name=$1
	branch=$2
	path="$BASE_DIR/$name"

	if git worktree list --porcelain | grep -Fxq "worktree $path"; then
		printf 'exists %s (%s)\n' "$path" "$branch"
		return
	fi

	if [ -e "$path" ]; then
		printf 'error %s: path exists but is not a registered worktree\n' "$path" >&2
		printf 'remove it or choose a different base directory: make ui-worktrees BASE_DIR=/tmp/tnview-ui\n' >&2
		exit 1
	fi

	if git show-ref --verify --quiet "refs/heads/$branch"; then
		git worktree add "$path" "$branch"
	else
		git worktree add -b "$branch" "$path" "$BASE_REF"
	fi
	printf 'created %s (%s)\n' "$path" "$branch"
}

printf 'UI worktree base: %s\n' "$BASE_DIR"
create_worktree tnview-ui-panels ui/panels
create_worktree tnview-ui-motion ui/motion
create_worktree tnview-ui-accessibility ui/accessibility
create_worktree tnview-ui-demo ui/demo

cat <<'EOF'

Suggested loop:
  cd ../tnview-ui-panels && make ui-snapshots
  cd ../tnview-ui-motion && make ui-snapshots
  cd ../tnview-ui-accessibility && make ui-review
  cd ../tnview-ui-demo && make ui-review
EOF
