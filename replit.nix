{pkgs}: {
  deps = [
    pkgs.python-launcher
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.glibcLocales
    pkgs.postgresql_16
  ];
}
