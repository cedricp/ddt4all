{
  description = "DDT4ALL - ECU diagnostic tool";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];

      forAllSystems = f: builtins.listToAttrs (map
        (system: {
          name = system;
          value = f system;
        })
        systems);
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowInsecurePredicate = pkg: builtins.elem (pkg.pname or pkg.name) [
              "qtwebkit"
            ];
          };

          python = pkgs.python3;
          
          # Python environment with all required packages
          python-with-deps = python.withPackages (ps: with ps; [
            pyusb
            pyserial
            crcmod
            setuptools
            wheel
            pip
            pyqt5
            pyqtwebengine
          ]);

          # System libraries needed for Qt
          systemLibs = [
            pkgs.stdenv.cc.cc.lib
            pkgs.glib
            pkgs.zlib
            pkgs.expat
            pkgs.libxkbcommon
            pkgs.dbus
            pkgs.krb5
            pkgs.xorg.libX11
            pkgs.xorg.libXext
            pkgs.xorg.libXrender
            pkgs.xorg.libXi
            pkgs.xorg.libXrandr
            pkgs.xorg.libXcursor
            pkgs.xorg.libXinerama
            pkgs.xorg.libXxf86vm
            pkgs.xorg.libXfixes
            pkgs.xorg.libXdamage
            pkgs.xorg.libXcomposite
            pkgs.xorg.libXtst
            pkgs.xorg.libXScrnSaver
            pkgs.xorg.libxcb
            pkgs.xorg.xcbutil
            pkgs.xorg.xcbutilwm
            pkgs.xorg.xcbutilimage
            pkgs.xorg.xcbutilkeysyms
            pkgs.xorg.xcbutilrenderutil
            pkgs.xorg.xcbutilcursor
            pkgs.libGL
            pkgs.libGLU
            pkgs.mesa
            pkgs.fontconfig
            pkgs.freetype
            pkgs.alsa-lib
            pkgs.pulseaudio
            pkgs.nss
            pkgs.nspr
            pkgs.wayland
            pkgs.wayland-protocols
          ];

        in
        {
          ddt4all = pkgs.stdenv.mkDerivation {
            pname = "ddt4all";
            version = "3.0.4";

            src = ./.;

            nativeBuildInputs = [
              pkgs.makeWrapper
              pkgs.qt5.wrapQtAppsHook
            ];

            buildInputs = [
              python-with-deps
              pkgs.qt5.full
            ] ++ systemLibs;

            # Don't build anything, just copy and wrap
            dontBuild = true;
            dontConfigure = true;

            installPhase = ''
              runHook preInstall

              # Create the application directory
              mkdir -p $out/share/ddt4all
              mkdir -p $out/bin

              # Copy all source files
              cp -r * $out/share/ddt4all/

              # Create the main executable script
              cat > $out/bin/ddt4all << 'EOF'
              #!/usr/bin/env bash
              cd $out/share/ddt4all
              exec ${python-with-deps}/bin/python main.py "$@"
              EOF

              chmod +x $out/bin/ddt4all

              runHook postInstall
            '';

            # Qt wrapping configuration
            postFixup = ''
              # Wrap the binary with Qt environment
              wrapProgram $out/bin/ddt4all \
                --set QT_PLUGIN_PATH "${pkgs.qt5.full}/lib/qt-5.15/plugins" \
                --set QT_QPA_PLATFORM_PLUGIN_PATH "${pkgs.qt5.full}/lib/qt-5.15/plugins/platforms" \
                --set QT_QPA_PLATFORM "xcb" \
                --set FONTCONFIG_FILE "${pkgs.fontconfig.out}/etc/fonts/fonts.conf" \
                --set FONTCONFIG_PATH "${pkgs.fontconfig.out}/etc/fonts" \
                --set QT_AUTO_SCREEN_SCALE_FACTOR "1" \
                --set QT_ENABLE_HIGHDPI_SCALING "1" \
                --set PYTHONDONTWRITEBYTECODE "1" \
                --prefix LD_LIBRARY_PATH : "${pkgs.lib.makeLibraryPath ([ pkgs.qt5.full ] ++ systemLibs)}" \
                --unset QT_IM_MODULE \
                --unset QT_SELECT \
                --unset QT_STYLE_OVERRIDE
            '';

            meta = with pkgs.lib; {
              description = "DDT4ALL - ECU diagnostic tool for automotive diagnostics";
              homepage = "https://github.com/cedricp/ddt4all";
              license = licenses.gpl3Plus;
              maintainers = [ ];
              platforms = platforms.linux;
              mainProgram = "ddt4all";
            };
          };

          default = self.packages.${system}.ddt4all;
        }
      );

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowInsecurePredicate = pkg: builtins.elem (pkg.pname or pkg.name) [
              "qtwebkit"
            ];
          };

          python = pkgs.python3;
          
          python-with-deps = python.withPackages (ps: with ps; [
            pyusb
            pyserial
            crcmod
            setuptools
            wheel
            pip
            pyqt5
            pyqtwebengine
          ]);

          systemLibs = [
            pkgs.stdenv.cc.cc.lib
            pkgs.glib
            pkgs.zlib
            pkgs.expat
            pkgs.libxkbcommon
            pkgs.dbus
            pkgs.krb5
            pkgs.xorg.libX11
            pkgs.xorg.libXext
            pkgs.xorg.libXrender
            pkgs.xorg.libXi
            pkgs.xorg.libXrandr
            pkgs.xorg.libXcursor
            pkgs.xorg.libXinerama
            pkgs.xorg.libXxf86vm
            pkgs.xorg.libXfixes
            pkgs.xorg.libXdamage
            pkgs.xorg.libXcomposite
            pkgs.xorg.libXtst
            pkgs.xorg.libXScrnSaver
            pkgs.xorg.libxcb
            pkgs.xorg.xcbutil
            pkgs.xorg.xcbutilwm
            pkgs.xorg.xcbutilimage
            pkgs.xorg.xcbutilkeysyms
            pkgs.xorg.xcbutilrenderutil
            pkgs.xorg.xcbutilcursor
            pkgs.libGL
            pkgs.libGLU
            pkgs.mesa
            pkgs.fontconfig
            pkgs.freetype
            pkgs.alsa-lib
            pkgs.pulseaudio
            pkgs.nss
            pkgs.nspr
            pkgs.wayland
            pkgs.wayland-protocols
          ];
        in
        {
          default = pkgs.mkShell {
            name = "ddt4all-dev-shell";

            buildInputs = [
              python-with-deps
              pkgs.qt5.full
              pkgs.git
            ] ++ systemLibs;

            shellHook = ''
              # Set up Qt environment for development
              export QT_PLUGIN_PATH="${pkgs.qt5.full}/lib/qt-5.15/plugins"
              export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.full}/lib/qt-5.15/plugins/platforms"
              export QT_QPA_PLATFORM="xcb"
              export DISPLAY=''${DISPLAY:-:0}
              export FONTCONFIG_FILE="${pkgs.fontconfig.out}/etc/fonts/fonts.conf"
              export FONTCONFIG_PATH="${pkgs.fontconfig.out}/etc/fonts"
              export QT_AUTO_SCREEN_SCALE_FACTOR=1
              export QT_ENABLE_HIGHDPI_SCALING=1
              export PYTHONDONTWRITEBYTECODE=1
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath ([ pkgs.qt5.full ] ++ systemLibs)}:$LD_LIBRARY_PATH"

              unset QT_IM_MODULE
              unset QT_SELECT
              unset QT_STYLE_OVERRIDE

              echo "=== DDT4All Development Environment ==="
              echo "Development shell ready. Run 'python main.py' to start."
              echo "Or build the package with 'nix build' and run with 'nix run .'"
              echo ""
            '';
          };
        }
      );

      # Make it runnable with `nix run`
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/ddt4all";
        };
        ddt4all = {
          type = "app";
          program = "${self.packages.${system}.ddt4all}/bin/ddt4all";
        };
      });
    };
}
