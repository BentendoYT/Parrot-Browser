.PHONY : bsys6_x86_64_linux_xz_artifact full_build_stage2_linux bsys6_x86_64_macos_dmg_artifact full_build_stage2_macos bsys6_x86_64_windows_zip_artifact full_build_stage2_windows bsys6_artifact full_build_generic

# This makefile just uses bsys6 to build the package we implicitly fully test
# that his source builds with the latest version of bsys6. So we also know that
# our docker images builds will succeed if this test succeeds.

bsys6_x86_64_linux_xz_artifact:

	rm -rf bsys6
	git clone "https://librewolf.dev/librewolf/bsys6.git"
	(cd bsys6 && ${MAKE} -f ../assets/testing.mk full_build_stage2_linux)
	cp -v bsys6/*.xz .
	cp -v "bsys6/SOURCEDIR/librewolf-$$(cat version)-$$(cat release)/mozconfig" mozconfig.txt
	rm -rf bsys6

full_build_stage2_linux:

	echo "[debug] Starting full_build_stage2_linux"

	echo "VERSION=$$(cat ../version)-$$(cat ../release)" > env.sh
	echo "WORKDIR=$$(pwd)/WORKDIR" >> env.sh
	echo "TARGET=linux" >> env.sh
	echo "ARCH=x86_64" >> env.sh
	echo "SOURCEDIR=$$(pwd)/SOURCEDIR/librewolf-$$(cat ../version)-$$(cat ../release)" >> env.sh
	cat env.sh

	mkdir WORKDIR
	mkdir SOURCEDIR
	(cd SOURCEDIR && tar xf ../../librewolf*.tar.gz)

	TARGET=linux ARCH=x86_64 ./bsys6 package

	@echo "[debug] Done full_build_stage2_linux"

# This code below is just block-copied from the linux case.

bsys6_x86_64_macos_dmg_artifact:

	rm -rf bsys6
	git clone "https://librewolf.dev/librewolf/bsys6.git"
	(cd bsys6 && ${MAKE} -f ../assets/testing.mk full_build_stage2_macos)
	cp -v bsys6/*.dmg .
	cp -v "bsys6/SOURCEDIR/librewolf-$$(cat version)-$$(cat release)/mozconfig" mozconfig.txt
	rm -rf bsys6

full_build_stage2_macos:

	echo "[debug] Starting full_build_stage2_macos"

	echo "VERSION=$$(cat ../version)-$$(cat ../release)" > env.sh
	echo "WORKDIR=$$(pwd)/WORKDIR" >> env.sh
	echo "TARGET=macos" >> env.sh
	echo "ARCH=x86_64" >> env.sh
	echo "SOURCEDIR=$$(pwd)/SOURCEDIR/librewolf-$$(cat ../version)-$$(cat ../release)" >> env.sh
	cat env.sh

	mkdir WORKDIR
	mkdir SOURCEDIR
	(cd SOURCEDIR && tar xf ../../librewolf*.tar.gz)

	TARGET=macos ARCH=x86_64 ./bsys6 package

	@echo "[debug] Done full_build_stage2_macos"

bsys6_x86_64_windows_zip_artifact:

	rm -rf bsys6
	git clone "https://librewolf.dev/librewolf/bsys6.git"
	(cd bsys6 && ${MAKE} -f ../assets/testing.mk full_build_stage2_windows)
	cp -v bsys6/*.zip .
	cp -v "bsys6/SOURCEDIR/librewolf-$$(cat version)-$$(cat release)/mozconfig" mozconfig.txt
	rm -rf bsys6

full_build_stage2_windows:

	echo "[debug] Starting full_build_stage2_windows"
	echo "VERSION=$$(cat ../version)-$$(cat ../release)" > env.sh
	echo "WORKDIR=$$(pwd)/WORKDIR" >> env.sh
	echo "TARGET=windows" >> env.sh
	echo "ARCH=x86_64" >> env.sh
	echo "SOURCEDIR=$$(pwd)/SOURCEDIR/librewolf-$$(cat ../version)-$$(cat ../release)" >> env.sh
	cat env.sh

	mkdir WORKDIR
	mkdir SOURCEDIR
	(cd SOURCEDIR && tar xf ../../librewolf*.tar.gz)

	TARGET=windows ARCH=x86_64 ./bsys6 package

	@echo "[debug] Done full_build_stage2_windows"

# Generic target for the platforms that have no dedicated target above (Windows/Linux on arm64, ...).
# Usage: make -f assets/testing.mk bsys6_artifact BSYS_TARGET=windows BSYS_ARCH=arm64 PKG_EXT=zip

bsys6_artifact:

	rm -rf bsys6
	git clone "https://librewolf.dev/librewolf/bsys6.git"
	(cd bsys6 && ${MAKE} -f ../assets/testing.mk full_build_generic BSYS_TARGET=$(BSYS_TARGET) BSYS_ARCH=$(BSYS_ARCH))
	cp -v bsys6/*.$(PKG_EXT) .
	cp -v "bsys6/SOURCEDIR/librewolf-$$(cat version)-$$(cat release)/mozconfig" mozconfig.txt
	rm -rf bsys6

full_build_generic:

	echo "[debug] Starting full_build_generic $(BSYS_TARGET) $(BSYS_ARCH)"
	echo "VERSION=$$(cat ../version)-$$(cat ../release)" > env.sh
	echo "WORKDIR=$$(pwd)/WORKDIR" >> env.sh
	echo "TARGET=$(BSYS_TARGET)" >> env.sh
	echo "ARCH=$(BSYS_ARCH)" >> env.sh
	echo "SOURCEDIR=$$(pwd)/SOURCEDIR/librewolf-$$(cat ../version)-$$(cat ../release)" >> env.sh
	cat env.sh

	mkdir WORKDIR
	mkdir SOURCEDIR
	(cd SOURCEDIR && tar xf ../../librewolf*.tar.gz)

	TARGET=$(BSYS_TARGET) ARCH=$(BSYS_ARCH) ./bsys6 package

	@echo "[debug] Done full_build_generic"
