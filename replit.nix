{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.openssl
    pkgs.libiconv
    pkgs.cargo
    pkgs.python-launcher
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.glibcLocales
    pkgs.postgresql_16
  ];
}
