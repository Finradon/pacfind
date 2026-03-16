import plistlib
from pathlib import Path

from pacfind_lib.backends.macos import MacOSApplicationsBackend


def make_app(
    root: Path,
    name: str,
    *,
    display_name: str | None = None,
    bundle_name: str | None = None,
    bundle_identifier: str | None = None,
) -> Path:
    app_path = root / f"{name}.app"
    info_path = app_path / "Contents" / "Info.plist"
    info_path.parent.mkdir(parents=True)
    payload = {}
    if display_name is not None:
        payload["CFBundleDisplayName"] = display_name
    if bundle_name is not None:
        payload["CFBundleName"] = bundle_name
    if bundle_identifier is not None:
        payload["CFBundleIdentifier"] = bundle_identifier
    with info_path.open("wb") as handle:
        plistlib.dump(payload, handle)
    return app_path


def test_is_available_only_on_macos(monkeypatch) -> None:
    monkeypatch.setattr("pacfind_lib.backends.macos.sys.platform", "darwin")
    assert MacOSApplicationsBackend().is_available() is True

    monkeypatch.setattr("pacfind_lib.backends.macos.sys.platform", "linux")
    assert MacOSApplicationsBackend().is_available() is False


def test_list_installed_reads_applications_and_user_applications(
    tmp_path, monkeypatch
) -> None:
    fake_home = tmp_path / "home"
    system_apps = tmp_path / "Applications"
    user_apps = fake_home / "Applications"
    fake_home.mkdir()
    system_apps.mkdir()
    user_apps.mkdir()

    make_app(
        system_apps,
        "Firefox",
        display_name="Firefox",
        bundle_identifier="org.mozilla.firefox",
    )
    make_app(
        user_apps,
        "Visual Studio Code",
        bundle_name="Visual Studio Code",
        bundle_identifier="com.microsoft.VSCode",
    )

    backend = MacOSApplicationsBackend(app_roots=[system_apps, user_apps])
    monkeypatch.setattr("pacfind_lib.backends.macos.Path.home", lambda: fake_home)
    results = backend.list_installed()

    assert [(result.name, result.source, result.detail) for result in results] == [
        ("Firefox", "applications", "org.mozilla.firefox"),
        ("Visual Studio Code", "user-applications", "com.microsoft.VSCode"),
    ]


def test_list_installed_falls_back_to_bundle_directory_name(tmp_path) -> None:
    apps = tmp_path / "Applications"
    apps.mkdir()
    (apps / "Simple App.app" / "Contents").mkdir(parents=True)

    backend = MacOSApplicationsBackend(app_roots=[apps])
    results = backend.list_installed()

    assert [(result.name, result.source) for result in results] == [
        ("Simple App", "applications")
    ]


def test_list_installed_ignores_nested_app_bundles(tmp_path) -> None:
    apps = tmp_path / "Applications"
    apps.mkdir()
    make_app(apps, "TopLevel", display_name="Top Level")
    nested_root = apps / "Container"
    nested_root.mkdir()
    make_app(nested_root, "Nested", display_name="Nested App")

    backend = MacOSApplicationsBackend(app_roots=[apps])
    results = backend.list_installed()

    assert [result.name for result in results] == ["Top Level"]
