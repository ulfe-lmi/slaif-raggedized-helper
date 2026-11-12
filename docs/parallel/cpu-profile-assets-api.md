# Installed CPU profile assets

The wheel contains byte-identical CPU v2, legacy CPU and GPU lock files under
`_worker_profiles`. CPU worker admission and CPU execution prediction select the
bundled CPU v2 lock and retain its pinned hash and metadata checks. A source
checkout in the `src/slaif_raggedized_helper` layout may use its fixed
`worker_profiles/cpu-v2/uv.lock` when no bundled asset tree exists, provided the
local project metadata identifies this project and the source directory does not
contain this package’s installed distribution metadata. A missing or
invalid installed asset is refused; no external installation-relative lock is
searched. Profile admission does not authorize model execution or qualify hardware.

The GPU lock is bundled, but the current GPU backend and launch plan still need
separate installed-layout compatibility work. This change does not establish GPU,
model, license, security, or deployment readiness.
