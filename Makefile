.PHONY: build clean distclean install uninstall
.PHONY: clean-mplayer distclean-mplayer mplayer
.PHONY: install-desktop install-icons install-mplayer install-osx-specific
.PHONY: uninstall-desktop uninstall-icons uninstall-mplayer

system := $(shell uname -s)
program_unix_name := pytee
modules := mplayer pycl pysd pytee subtitles

ifeq ($(system),Darwin)
PREFIX := /Applications
appdir := $(PREFIX)/$(program_unix_name).app
contentsdir := $(appdir)/Contents
bindir := $(contentsdir)/MacOS
datarootdir := $(contentsdir)/Resources
datadir := $(datarootdir)
mplayer_srcdir := osx/mplayer
else
PREFIX := /usr
bindir := $(PREFIX)/bin
datarootdir := $(PREFIX)/share
datadir := $(datarootdir)/$(program_unix_name)
endif
execpath := $(bindir)/$(program_unix_name)


build:

install: build
	set -e; for file in $$(find $(modules) -name '*.py') $$(find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(datadir)/$$(dirname $$file); \
		install -m 0644 $$file $(DESTDIR)$(datadir)/$$file; \
	done
	install -d $(DESTDIR)$(bindir)
	echo '#!/bin/sh'> $(DESTDIR)$(execpath)
	echo '# Runs pytee python script' >> $(DESTDIR)$(execpath)
	echo >> $(DESTDIR)$(execpath)
ifeq ($(system),Darwin)
	echo '# Include default Mac ports path' >> $(DESTDIR)$(execpath)
	echo 'export PATH=/opt/local/bin:/opt/local/sbin:$$PATH' >> $(DESTDIR)$(execpath)
endif
	echo 'exec $(datadir)/$(program_unix_name)/main.py "$$@"' >> $(DESTDIR)$(execpath)
	chmod a+x $(DESTDIR)$(datadir)/$(program_unix_name)/main.py $(DESTDIR)$(execpath)

clean:
	rm -f $$(find $(modules) -name '*.pyc')

distclean: clean


ifeq ($(system),Darwin)
build: mplayer
clean: clean-mplayer
distclean: distclean-mplayer
install: install-mplayer install-osx-specific

mplayer: $(mplayer_srcdir)/config.mak
	make -C $(mplayer_srcdir) -j4

$(mplayer_srcdir)/config.mak: Makefile
	cd $(mplayer_srcdir) && ./configure --prefix=$(datadir)/mplayer --bindir=$(bindir) \
		--disable-mencoder --disable-dvdread --disable-dvdread-internal --disable-networking --disable-protocol=sctp

install-mplayer: mplayer
	make -C $(mplayer_srcdir) install

install-osx-specific:
	install -d $(DESTDIR)$(contentsdir)
	install -m 0644 osx/Info.plist $(DESTDIR)$(contentsdir)/Info.plist
	install -d $(DESTDIR)$(datarootdir)
	install -m 0644 osx/$(program_unix_name).icns $(DESTDIR)$(datarootdir)/$(program_unix_name).icns
	install -d $(DESTDIR)$(datadir)
	install -m 0644 osx/argv_emulation.py $(DESTDIR)$(datadir)/argv_emulation.py

uninstall: uninstall-mplayer
	rm -rf $(appdir)

uninstall-mplayer:
	make -C $(mplayer_srcdir) uninstall

clean-mplayer:
	make -C $(mplayer_srcdir) clean

distclean-mplayer:
	make -C $(mplayer_srcdir) distclean
else
install: install-desktop install-icons

install-desktop:
	install -d $(DESTDIR)$(datarootdir)/applications
	install -m 0644 $(program_unix_name).desktop $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop

install-icons:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(datarootdir)/icons/hicolor/$$(dirname $${file#*/}); \
		install -m 0644 $$file $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done

uninstall: uninstall-desktop uninstall-icons
	set -e; $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datadir)/$${file}; \
	done
	set -e; for file in $$(find $(modules) -name '*.py'); do \
		rm -f $(DESTDIR)$(datadir)/$${file}{,c}; \
	done
	set -e; while true; do \
		[ -d "$(DESTDIR)$(datadir)" ] || break; \
		dirs="$$(find $(DESTDIR)$(datadir) -type d -empty)"; \
		[ -n "$$dirs" ] || break; \
		rmdir $$dirs; \
	done
	rm -f $(DESTDIR)$(bindir)/$(program_unix_name)

uninstall-desktop:
	rm -f $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop

uninstall-icons:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done
endif
