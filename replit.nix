{pkgs}: {
  deps = [
    pkgs.imagemagick_light
    pkgs.yakut
    pkgs.lsof
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
  env = {
    PGVERSION = "16.4";  # PostgreSQLのバージョンを明示
  };
}
