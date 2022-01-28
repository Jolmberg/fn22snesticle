menu.sfc: menu.o lorom128.cfg
	ld65 -C lorom128.cfg -o $@ $< --dbgfile menu.dbg

menu.o: menu.s font.inc wave.inc sin.inc cos.inc
	ca65 --debug-info $<

font.inc: spof.py
	if [ -z "$(FIGHTNIGHT)" ]; then \
	  ./spof.py /dev/zero > $@; \
	else \
	  ./spof.py "$(FIGHTNIGHT)" > $@; \
	fi

wave.inc: wave.py
	./wave.py 10 28 85 > $@

sin.inc: sine.py
	./sine.py 0 16 4095 > $@

cos.inc: sine.py
	./sine.py 16 80 4095 > $@

.PHONY: clean
clean:
	rm -f menu.sfc menu.o menu.dbg font.inc wave.inc sin.inc cos.inc
