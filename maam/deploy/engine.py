import os
import shutil
from pathlib import Path
from typing import Optional

from maam.config.models import (
    AssetKind,
    DeploymentMode,
    DeploymentRecord,
    DeploymentStatus,
)


class DeploymentEngine:
    def deploy_asset(
        self,
        name: str,
        kind: AssetKind,
        tool: str,
        source: Path,
        target_dir: Path,
        mode_preference: DeploymentMode = DeploymentMode.SYMLINK,
    ) -> DeploymentRecord:
        """
        Materialize an asset into a target tool directory.
        Deploys as <target_dir>/<name> (or <target_dir>/<name>.<ext> for files).
        """
        target = target_dir / name
        if source.is_file() and source.suffix:
            if not target.name.endswith(source.suffix):
                target = target.with_suffix(source.suffix)

        target_dir.mkdir(parents=True, exist_ok=True)

        # Check if already correct symlink or file
        if target.is_symlink():
            if os.path.realpath(target) == os.path.realpath(source):
                return DeploymentRecord(
                    asset_name=name,
                    asset_kind=kind,
                    tool=tool,
                    source=str(source),
                    target=str(target),
                    mode=DeploymentMode.SYMLINK,
                    status=DeploymentStatus.ACTIVE,
                )
        elif target.exists() and mode_preference == DeploymentMode.COPY:
            # For simplicity, if we want COPY and it exists, we'll re-copy to be sure
            pass

        # Remove existing target if it exists and is different
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()

        actual_mode = mode_preference
        try:
            if mode_preference == DeploymentMode.SYMLINK:
                # Use absolute path for symlink target for reliability
                os.symlink(source.resolve(), target)
            else:
                if source.is_dir():
                    shutil.copytree(source, target, symlinks=True)
                else:
                    shutil.copy2(source, target)
        except (OSError, shutil.Error):
            if mode_preference == DeploymentMode.SYMLINK:
                # Fallback to copy
                if source.is_dir():
                    shutil.copytree(source, target, symlinks=True)
                else:
                    shutil.copy2(source, target)
                actual_mode = DeploymentMode.COPY
            else:
                raise

        return DeploymentRecord(
            asset_name=name,
            asset_kind=kind,
            tool=tool,
            source=str(source),
            target=str(target),
            mode=actual_mode,
            status=DeploymentStatus.ACTIVE,
        )

    def remove_deployment(self, record: DeploymentRecord):
        """
        Safely remove a realized deployment.
        """
        target = Path(record.target)
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
