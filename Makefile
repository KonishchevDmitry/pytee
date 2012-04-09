.PHONY: all build clean distclean install uninstall
.PHONY: clean-mplayer distclean-mplayer mplayer
.PHONY: install-desktop install-icons install-mplayer
.PHONY: uninstall-desktop uninstall-icons uninstall-mplayer

program_unix_name := pytee

PREFIX := /usr
bindir := $(PREFIX)/bin
datarootdir := $(PREFIX)/share
libexecdir := $(PREFIX)/libexec
datadir := $(datarootdir)/$(program_unix_name)

mplayer_srcdir := mplayer/mplayer
mplayer_dir := $(libexecdir)/$(program_unix_name)

system := $(shell uname -s)


all: build

ifeq ($(system),Darwin)
build: mplayer
clean: clean-mplayer
distclean: distclean-mplayer
install: install-mplayer
uninstall: uninstall-mplayer
else
install: install-desktop install-icons
uninstall: uninstall-desktop uninstall-icons
endif


build:

mplayer: $(mplayer_srcdir)/config.mak
	make -C $(mplayer_srcdir) -j4

$(mplayer_srcdir)/config.mak: Makefile
	cd $(mplayer_srcdir) && ./configure --prefix=$(mplayer_dir) --bindir=$(mplayer_dir) \
		--disable-mencoder --disable-dvdread --disable-dvdread-internal --disable-networking


install: build
	set -e; for file in mplayer/*.py $$(find pycl pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(datadir)/$$(dirname $$file); \
		install -m 0644 $$file $(DESTDIR)$(datadir)/$$file; \
	done
	install -d $(DESTDIR)$(bindir)
	echo '#!/bin/sh\nexec $(datadir)/$(program_unix_name)/main.py "$$@"' > $(DESTDIR)$(bindir)/$(program_unix_name)
	chmod a+x $(DESTDIR)$(datadir)/$(program_unix_name)/main.py
	chmod a+x $(DESTDIR)$(bindir)/$(program_unix_name)

install-desktop:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(datarootdir)/icons/hicolor/$$(dirname $${file#*/}); \
		install -m 0644 $$file $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done

install-icons:
	install -d $(DESTDIR)$(datarootdir)/applications
	install -m 0644 $(program_unix_name).desktop $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop

install-mplayer: mplayer
	make -C $(mplayer_srcdir) install


uninstall:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datadir)/$$file; \
	done
	set -e; for file in mplayer/*.py $$(find pycl pysd pytee subtitles -name '*.py'); do \
		rm -f $(DESTDIR)$(datadir)/$${file}{,c}; \
	done
	set -e; for dir in $(DESTDIR)$(datadir) $(DESTDIR)$(mplayer_dir); do \
		while true; do \
			[ -d "$$dir" ] || break; \
			dirs="$$(find $$dir -type d -empty)"; \
			[ -n "$$dirs" ] || break; \
			rmdir $$dirs; \
		done; \
	done
	rm -f $(DESTDIR)$(bindir)/$(program_unix_name)

uninstall-desktop:
	rm -f $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop

uninstall-icons:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done

uninstall-mplayer:
	make -C $(mplayer_srcdir) uninstall


clean:

clean-mplayer:
	make -C $(mplayer_srcdir) clean


distclean:

distclean-mplayer:
	make -C $(mplayer_srcdir) distclean
