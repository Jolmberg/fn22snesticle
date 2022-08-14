.p816
.i16
.a8

.segment "HEADER"               ; +$7FE0 in file
    .byte "SNESTICLE MENU"      ; ROM name

.segment "ROMINFO"              ; +$7FD5 in file
    .byte $30                   ; LoROM, fast-capable
    .byte 0                     ; no battery RAM
    .byte $07                   ; 128K ROM
    .byte 0,0,0,0
    .word $AAAA,$5555           ; dummy checksum and complement

.segment "VECTORS"
    .word 0, 0, 0, 0, 0, vblank, 0, 0
    .word 0, 0, 0, 0, 0, 0, reset, 0

.segment "ZEROPAGE"

temp1: .res 2
temp2: .res 2
temp3: .res 2
temp4: .res 2
temp5: .res 2
temp6: .res 2
temp7: .res 2
temp8: .res 2

chosen: .res 4
controllers: .res 4

cgame: .res 2
csetting: .res 2
cy: .res 1
cy_games: .res 1
cy_settings: .res 1
btn: .res 1
btn_new: .res 1
btn_active: .res 1
btn_cooldown: .res 1
col_ind:
col_r_ind: .res 1
col_g_ind: .res 1
col_b_ind: .res 1
col_dir:
col_r_dir: .res 1
col_g_dir: .res 1
col_b_dir: .res 1
col_val:
col_r_val: .res 1
col_g_val: .res 1
col_b_val: .res 1
dummy: .res 1
newcol: .res 2
dummy2: .res 2
page: .res 2
strobe1: .res 2
strobe2: .res 2
transition: .res 1
scroll_x: .res 2
copysrc: .res 2
copydest: .res 2
screen_base: .res 2
.segment "BSS"
spritesinram: .res 512
starxy: .res 512
starspdxy: .res 512
starage: .res 256
starcount: .res 2

.segment "CODE"

reset:
    sei
    clc
    xce
    rep #$18
    ldx #$1FF
    txs                      ; Set stack pointer to $1ff
    lda #$80                 ; screen off
    sta $2100
    stz $2101
    stz $2102
    stz $2103
    stz $2105
    stz $2106
    stz $2107
    stz $2108
    stz $2109
    stz $210A
    stz $210B
    stz $210C
    stz $210D
    stz $210D
    lda #$FF
    sta $210E
    sta $2110
    sta $2112
    sta $2114
    lda #$07
    sta $210E
    sta $2110
    sta $2112
    sta $2114
    stz $210F
    stz $210F
    stz $2111
    stz $2111
    stz $2113
    stz $2113
    lda #$80
    sta $2115
    stz $2116
    stz $2117
    stz $211A
    stz $211B
    lda #$01
    sta $211B
    stz $211C
    stz $211C
    stz $211D
    stz $211D
    stz $211E
    sta $211E
    stz $211F
    stz $211F
    stz $2120
    stz $2120
    stz $2121
    stz $2123
    stz $2124
    stz $2125
    stz $2126
    stz $2127
    stz $2128
    stz $2129
    stz $212A
    stz $212B
    stz $212C
    stz $212D
    stz $212E
    stz $212F
    lda #$30
    sta $2130
    stz $2131
    lda #$E0
    sta $2132
    stz $2133
    stz $4200
    lda #$FF
    sta $4201
    stz $4202
    stz $4203
    stz $4204
    stz $4205
    stz $4206
    stz $4207
    stz $4208
    stz $4209
    stz $420A
    stz $420B
    stz $420C
    stz $420D

    ;; Copy bg, font and sprites to tiles
    ldy #0                      ; Destination offset 0
    sty $2116
    lda #1
    sta $4300
    lda #$18                    ; Write register is $2118
    sta $4301
    ldy #bgdata                 ; Source address
    sty $4302
    stz $4304                   ; Source bank is 0
    lda #$80                    ; Size
    sta $4305
    lda #$D
    sta $4306
    lda #1
    sta $420b

    ;; Copy palette
    stz $2121                   ; Destination offset 0
    stz $4300                   ; transfer mode 0
    lda #$22
    sta $4301                   ; Register $2122, cgram data
    ldy #bgpalette              ; Source address
    sty $4302
    stz $4304                   ; Source bank is 0
    ldy #256                    ; Size (128 colours)
    sty $4305
    lda #1
    sta $420b

    ldy #sprpalette
    sty $4302
    ldy #256
    sty $4305
    sta $420b

    ;; Display title
    lda #0
    ldy #title
    sty $0
    ldy #$2000
    ldx #$100
    jsr copyscreen

    ;; Display first screen of games
    lda #1
    ldy #$8000
    sty $0
    ldy #$2080
    ldx #$5c0
    jsr copyscreen

    ;; Blank lines (including second screen)
    ldy #$2360
    sty $2116
    lda #9                      ; word, fixed
    sta $4300
    lda #$18
    sta $4301
    ldy #empty
    sty $4302
    lda #0
    sta $4304
    ldx #$940
    stx $4305
    lda #1
    sta $420b

    lda #0
    ldy #settings_title
    sty $0
    ldy #$2400
    ldx #$200
    jsr copyscreen

    lda #0
    sta $2105                   ; mode 0
    stz $210b                   ; BG1,2 tiledata offset (0)
    lda #$21
    sta $2107                   ; BG1 tilemap offset ($4000)

    ;; Reset sprites
    ldx #$1f8
:
    stz starage, x
    stz starage + 2, x
    lda #1
    sta starage + 1, x
    sta starage + 3, x
    lda #%00000010
    sta spritesinram + 3, x
    lda #39
    sta spritesinram + 2, x
    lda #224
    sta spritesinram + 1, x
    stz spritesinram + 0, x
    dex
    dex
    dex
    dex
    bpl :-

    ;; DMA lower sprite table
    stz $4300
    lda #4
    sta $4301
    ldy #spritesinram
    sty $4302
    stz $4304
    ldy #$200
    sty $4305
    lda #1
    sta $420b
    ;; Upper table
    lda #8
    sta $4300
    ldy #zero
    sty $4302
    ldy #$20
    sty $4305
    lda #1
    sta $420b

    lda #6                      ; arrow x position
    sta spritesinram + 508
    lda #$20                    ; arrow y position
    sta spritesinram + 509
    lda #$59                    ; arrow tile
    sta spritesinram + 510
    lda #%00100000              ; arrow palette
    sta spritesinram + 511

    stz strobe1
    stz strobe2
    ;; Reset stars
    rep #$20
.a16
    ldx #$1f8
@resetstarloop:
    lda $8000, x
    sta starxy, x
    lda $8200, x
    ora #$0100
    sta starspdxy, x
    stz starspdxy + 2, x
    lda #$F800
    sta starxy + 2, x
    dex
    dex
    dex
    dex
    bpl @resetstarloop
    lda #0
    sep #$20
.a8
    lda #$11                    ; sprites and bg1 active
    sta $212c                   ; main screen layers

    lda #1
    sta col_r_dir
    sta col_g_dir
    lda #$ff
    sta col_b_dir
    stz col_r_ind
    lda #170
    sta col_g_ind
    lda #171
    sta col_b_ind
    

    stz cgame                   ; Game number
    stz cgame + 1
    stz csetting
    stz csetting + 1
    lda #4
    sta cy_games
    sta cy_settings
    lda #1
    sta controllers
    sta controllers + 1
    sta controllers + 2
    sta controllers + 3
    ldy #$8000
    sty page

    lda filenames
    sta chosen
    lda filenames + 1
    sta chosen + 1
    lda filenames + 2
    sta chosen + 2
    lda filenames + 3
    sta chosen + 3
    ldy #$007f
    sty starcount

    jsr movestars
    lda #$0f                    ; Maximum screen brightness
    sta $2100

    lda #$81
    sta $4200
    ldx #0
    stx scroll_x
    lda #0
    sta transition
    ldx #$2000
    stx screen_base
    jmp wait_for_vblank

mainloop:
    jsr colourcycle
    jsr movestars
    jsr update_scroll
    lda transition
    bit #1
    beq check_buttons
    jmp wait_for_vblank

check_buttons:
    lda $4219
    and #$af                    ; Check for directions, select, and B
    bne direction_pressed
    lda #0
    sta btn
    sta btn_cooldown
    jmp wait_for_vblank

direction_pressed:
    sta btn_new
    eor btn
    and btn_new
    bne new_btn
    lda btn
    and btn_new
    sta btn
    lda btn_new
    and btn_active
    bne :+
    sta btn
    jmp wait_for_vblank
:   lda btn_cooldown
    dec
    sta btn_cooldown
    beq :+
    jmp wait_for_vblank
:
    lda #6
    sta btn_cooldown
    bpl handle_btn              ; Always taken

new_btn:
    sta btn_active
    lda #30
    sta btn_cooldown
    lda btn_new
    sta btn

handle_btn:
    lda btn_active
    bit #$20
    beq :+
    jmp handle_btn_select
:
    bit #8
    beq :+
    jmp handle_btn_up
:
    bit #4
    beq :+
    jmp handle_btn_down
:
    bit #2
    bne handle_btn_left
    bit #1
    bne handle_btn_right
    bit #$80
    beq :+
    jmp handle_btn_b
:

handle_btn_right:
    lda transition
    beq handle_btn_right_main
    jmp wait_for_vblank
handle_btn_right_main:
    rep #$20
.a16
    lda cgame
    clc
    adc #23
    cmp maxgame
    beq :+
    bpl :++
:
    sta cgame
    jsr nextpage
:
    lda #0
    sep #$20
.a8
    lda cy_games
    jmp update_chosen

handle_btn_left:
    lda transition
    beq handle_btn_left_main
    jmp wait_for_vblank
handle_btn_left_main:
    rep #$20
.a16
    lda cgame
    sec
    sbc #23
    bmi :+
    sta cgame
    jsr prevpage
:
    lda #0
    sep #$20
.a8
    lda cy_games
    jmp update_chosen

handle_btn_up:
    lda transition
    beq handle_btn_up_main
handle_btn_up_settings:
    ldy csetting
    bne :+
    jmp wait_for_vblank
:
    dey
    sty csetting
    lda cy_settings
    dec
    sta cy_settings
    jmp update_chosen

handle_btn_up_main:
    ldy cgame
    bne :+
    jmp wait_for_vblank
:
    dey
    sty cgame
    lda cy_games
    dec
    cmp #3
    beq :+
    sta cy_games
    jmp update_chosen
:
    rep #$20
.a16
    jsr prevpage
    sep #$20
.a8
    sta cy_games
    jmp update_chosen
handle_btn_down:
    lda transition
    beq handle_btn_down_main
handle_btn_down_settings:
    ldy csetting
    cpy #3
    bne :+
    jmp wait_for_vblank
:
    iny
    sty csetting
    lda cy_settings
    inc
    sta cy_settings
    jmp update_chosen

handle_btn_down_main:
    ldy cgame                   ; It's down
    cpy maxgame
    bne :+
    jmp wait_for_vblank
:
    iny
    sty cgame
    lda cy_games
    inc
    cmp #27
    beq :+
    sta cy_games
    jmp update_chosen
:
    rep #$20
.a16
    jsr nextpage
    sep #$20
.a8
    sta cy_games
    jmp update_chosen

handle_btn_select:
    lda transition
    inc
    and #3
    sta transition
    ldx scroll_x
    dec a
    bne :+
    ldx #4
    bra :++
:   eor #2
    bne :++
    ldx #$fc
:   stx scroll_x
:   lda screen_base + 1
    eor #$4
    sta screen_base + 1
    jmp wait_for_vblank

handle_btn_b:
    lda transition
    eor #2
    bne wait_for_vblank
    ldx csetting
    lda controllers, x
    inc a
    cmp #3
    bne :+
    lda #0
:
    sta controllers, x
    jmp wait_for_vblank

update_chosen:
    asl a
    asl a
    asl a
    sta spritesinram + 509      ; Move arrow
    rep #$20
.a16
    lda cgame
    asl a
    asl a
    tay
    lda #0
    sep #$20
.a8
    lda filenames, y
    sta chosen
    lda filenames + 1, y
    sta chosen + 1
    lda filenames + 2, y
    sta chosen + 2
    lda filenames + 3, y
    sta chosen + 3
wait_for_vblank:
    wai
    jmp mainloop

.a16
nextpage:
    lda page
    clc
    adc #$5c0
    sta page
    lda #4
    rts

prevpage:
    lda page
    sec
    sbc #$5c0
    sta page
    lda #26
    rts
.a8

;; A = source bank, $0 = source offset, Y = destination, X = size
copyscreen:
    xba
    sty $2116
    lda #1
    sta $4300
    lda #$18
    sta $4301
    ldy $0
    sty $4302
    lda #0
    xba
    sta $4304
    stx $4305
    lda #1
    sta $420b
    rts

colourcycle:
    ldx #2
colourcycle_loop:
    lda col_ind, x
    clc
    adc col_dir, x
    cmp #$ff
    bne colourcycle_ok
    lda col_dir, x
    eor #$fe
    sta col_dir, x
    clc
    adc col_ind, x
colourcycle_ok:
    sta col_ind, x
    tay
    lda wave, y
    sta col_val, x
    dex
    bpl colourcycle_loop
    lda col_g_val
    tay
    lsr a
    lsr a
    lsr a
    sta temp1
    lda col_b_val
    asl a
    asl a
    ora temp1
    sta newcol + 1
    tya
    asl a
    asl a
    asl a
    asl a
    asl a
    ora col_r_val
    sta newcol
    rts

update_scroll:
    lda transition
    bit #1
    beq end_scroll
    ldx scroll_x
    bit #2
    beq scroll_right
scroll_left:
    dex
    dex
    dex
    dex
    dex
    dex
    stx scroll_x
    lda scroll_x
    bne end_scroll
    beq end_transition
scroll_right:
    inx
    inx
    inx
    inx
    inx
    inx
    stx scroll_x
    lda scroll_x
    bne end_scroll

end_transition:
    lda transition
    inc a
    and #3
    sta transition

end_scroll:
    rts

movestars:
    rep #$20
.a16
    lda starcount
    dec a
    asl
    asl
    tax
    ldy #2
@movestarloop:
    lda starspdxy, x
    bmi @neg
    and #$ff00
    bpl @doit
@neg:
    ora #$00ff
@doit:
    xba
    pha
    ;; Go faster
    sta temp2
    clc
    adc temp2
    clc
    adc starspdxy, x
    bvs @toobig
    sta starspdxy, x
@toobig:
    pla
    ;; Go faster
    sta temp2
    clc
    adc temp2
    clc
    adc starxy, x
    sta temp1
    eor starxy, x
    bpl @onscreen
    ;; Reset this star
    txa
    pha
    lsr
    and #$fe
    tax
    stz starage, x
    pla
    tax

@onscreen:
    lda temp1
    sta starxy, x
    xba
    sep #$20
.a8
    dey
    bne @flork
    sta spritesinram - 1, x
    ldy #2
    bpl :+
@flork:
    sta spritesinram, x
:
    rep #$20
.a16
    dex
    dex
    bpl @movestarloop

    ;; Age stars
    ldx #$fc
    ldy #$1f8
@ageloop:
    lda starage, x
    bne @notnew

    txa
    pha
    lsr
    and #$fe
    tax
    lda sin, x
    sta temp1
    lda cos, x
    sta temp2
    pla
    tax

    ;; Reset this star
    lda temp1                   ; sin
    sta starspdxy + 2, y
    ;; Randomize
    bit strobe1
    bmi @flobb
    clc
    adc temp1                   ; sin
    bit strobe2
    bmi @flobb
    clc
    adc temp1                   ; sin
@flobb:
    clc
    adc #$8000
    sta starxy + 2, y
    lda temp2                   ; cos
    sta starspdxy, y
    ;; Randomize
    bit strobe1
    bmi @flobb2
    clc
    adc temp2                   ; cos
    bit strobe2
    bmi @flobb2
    clc
    adc temp2                   ; cos
@flobb2:
    clc
    adc #$8000
    sta starxy, y
    lda strobe1
    eor #$8000
    sta strobe1
    lda #$0100
@notnew:
    ;; Store to sprite map
    pha
    sep #$20
.a8
    xba
    clc
    adc #$5a
    sta spritesinram + 2, y
    rep #$20
.a16
    pla
    clc
    adc #$a                     ; Increase age
    bit #$1000
    bne @toobig2
    sta starage, x
@toobig2:
    dex
    dex
    bpl @notzero
    ldx #$7f
@notzero:
    dey
    dey
    dey
    dey
    bpl @ageloop

    lda #0
    sep #$20
.a8
    rts

copy_controller_settings:
    rep #$20
.a16
    lda controllers, x
    and #$ff
    asl a
    asl a
    asl a
    asl a
    clc
    adc #controller_off
    sta temp1
    lda #0
    txa
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc #$2490
    tay
    lda #16
    tax
    lda #0
    sep #$20
    jsr copyscreen
.a8
    rts

vblank:
    lda transition
    and #2
    beq :+
    lda cy_settings
    bne :++
:
    lda cy_games
:
    sta cy
    lda scroll_x
    sta $210D
    lda scroll_x + 1
    sta $210D
    ;; Toggle strobe
    lda strobe2 + 1
    eor #$80
    sta strobe2 + 1
    ;; Increase star count (not really needed)
    lda starcount
    inc a
    bmi @enoughstars
    sta starcount
@enoughstars:
    ;; Update arrow position
    lda transition
    and #1
    beq :+
    lda #$f0
    bra :++
:   lda cy
    asl a
    asl a
    asl a
:   sta spritesinram + 509

    ;; DMA all 128 sprites
    stz $2102
    stz $4300
    lda #4
    sta $4301
    ldy #spritesinram
    sty $4302
    stz $4304
    ldy #$200
    sty $4305
    lda #1
    sta $420b
    sta $4300

    lda transition
    and #2
    beq copy_game_list
copy_settings:
    lda #0
    ldy #settings
    sty temp1
    ldy #$2480
    ldx #$100
    jsr copyscreen

    ldx #0
    jsr copy_controller_settings
    ldx #1
    jsr copy_controller_settings
    ldx #2
    jsr copy_controller_settings
    ldx #3
    jsr copy_controller_settings
    jmp no_copy_needed
copy_game_list:
    lda #1
    ldy page
    sty temp1
    ldy #$2080
    ldx #$5c0
    jsr copyscreen
no_copy_needed:
    ;; Highlight selected
    lda transition
    and #1
    bne no_highlight
    lda cy
    xba
    rep #$20
.a16
    lsr a
    lsr a
    lsr a
    clc
    adc screen_base
    tay
    lda #0
    sep #$20
.a8
    sty $2116
    ldx #8
    lda #4
:   sta $2119
    sta $2119
    sta $2119
    sta $2119
    dex
    bne :-

no_highlight:
    ;; Update palettes
    lda #$8f                    ; Last entry of sprite palette 0
    sta $2121                   ; $2121 cgram address
    lda newcol
    sta $2122                   ; $2122 cgram data
    lda newcol + 1
    sta $2122
    lda #6                      ; Entry 2 of bg palette 1
    sta $2121
    lda newcol
    sta $2122
    lda newcol + 1
    sta $2122
    rep #$20
.a16
    lda newcol
    clc
    adc #%0000110001100011
    sep #$20
.a8
    sta $2122
    lda #0
    xba
    sta $2122

    bit $4210
    rti


.segment "RODATA"
datastart:
    .byte "data"
bgpalette:
    .word 0, %0011110000000000, %0110111101111011, %0110111101111011
    .word 0, %0011110000000000, 0, 0
    .word 0, %0011110000000000, 0, %0111111111111111
sprpalette:
    .word 0,%0011110000011111,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f,$3c1f
    .word 0,%0000100001000010,%0001000010000100,%0001100011000110,%0010000100001000
    .word %0010100101001010,%0011000110001100,%0011100111001110,%0100001000010000
    .word %0100101001010010,%0101001010010100,%0101101011010110,%0110001100011000
    .word %0110101101011010,%0111001110011100,%0111101111011110
wave:
    .include "wave.inc"
sin:
    .include "sin.inc"
cos:
    .include "cos.inc"
title:
    .byte $20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8
    .byte $20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8
    .byte $20,8,$1,8,$2,8,$3,8,$4,8,$5,8,$6,8,$7,8,$8,8,$9,8,$a,8,$b,8,$c,8,$d,8,$e,8,$f,8,$10,8,$11,8,$12,8,$13,8,$14,8,$15,8,$16,8,$17,8,$18,8,$19,8,$1a,8,$1b,8,$1c,8,$1d,8,$1e,8,$1f,8,$20,8,$21,8,$22,8,$23,8,$24,8,$25,8,$26,8,$27,8,$28,8,$29,8,$2a,8,$2b,8,$2c,8,$2d,8,$2e,8,$2f,8,$30,8,$31,8,$32,8,$33,8,$34,8,$35,8,$36,8,$37,8,$38,8,$39,8,$3a,8,$3b,8,$3f,8,$d5,8,$d6,8,$3e,8
    .byte $D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8
    .byte $D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8
empty:
    .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
settings_title:
    .byte $20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8
    .byte $20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8,$20,8
    .byte $40,8,$41,8,$42,8,$43,8,$44,8,$45,8,$46,8,$47,8,$48,8,$49,8,$4a,8,$4b,8,$4c,8,$4d,8,$4e,8,$4f,8,$50,8,$51,8,$52,8,$53,8,$54,8,$55,8,$56,8,$57,8,$58,8,$59,8,$5a,8,$5b,8,$5c,8,$5d,8,$5e,8,$5f,8
    .byte $60,8,$d7,8,$d5,8,$63,8,$64,8,$65,8,$66,8,$67,8,$68,8,$69,8,$6a,8,$6b,8,$6c,8,$6d,8,$6e,8,$6f,8,$70,8,$71,8,$72,8,$73,8,$74,8,$75,8,$76,8,$77,8,$78,8,$79,8,$7a,8,$7b,8,$7c,8,$7d,8,$7e,8,$7f,8
    .byte $D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8
    .byte $D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8,$D4,8
settings:
    .word 0,0,$8c,$98,$97,$9d,$9b,$98,$95,$95,$8e,$9b,0,$81,$a9,0,$9c,$8e,$97,$9c,$92,$8b,$95,$8e,0,0,0,0,0,0,0,0
    .word 0,0,$8c,$98,$97,$9d,$9b,$98,$95,$95,$8e,$9b,0,$82,$a9,0,$9c,$8e,$97,$9c,$92,$8b,$95,$8e,0,0,0,0,0,0,0,0
    .word 0,0,$8c,$98,$97,$9d,$9b,$98,$95,$95,$8e,$9b,0,$83,$a9,0,$9c,$8e,$97,$9c,$92,$8b,$95,$8e,0,0,0,0,0,0,0,0
    .word 0,0,$8c,$98,$97,$9d,$9b,$98,$95,$95,$8e,$9b,0,$84,$a9,0,$9c,$8e,$97,$9c,$92,$8b,$95,$8e,0,0,0,0,0,0,0,0
controller_off:
    .word $98,$8f,$8f,0,0,0,0,0
controller_sensible:
    .word $9c,$8e,$97,$9c,$92,$8b,$95,$8e
controller_literal:
    .word $95,$92,$9d,$8e,$9b,$8a,$95,0
.segment "BG"
bgdata:
.segment "FONT"
font:
    .include "font.inc"
    .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
sprites:
sprite_arrow:
    .byte %00001000,%00001000
    .byte %00001100,%00001100
    .byte %11111110,%11111110
    .byte %11111111,%11111111
    .byte %11111110,%11111110
    .byte %00001100,%00001100
    .byte %00001000,%00001000
    .byte %00000000,%00000000
    .byte %00001000,%00001000
    .byte %00001100,%00001100
    .byte %11111110,%11111110
    .byte %11111111,%11111111
    .byte %11111110,%11111110
    .byte %00001100,%00001100
    .byte %00001000,%00001000
    .byte %00000000,%00000000
sprite_star:
    .byte   0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte   0,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    .byte $80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,$80,$80,0,0,0,0,0,0,0,0,0,0,0,0,0,0
top_bar:
    .byte $ff,0,$ff,0,0,0,0,0,0,0,0,0,0,0,0,0
button_z:
    .word $7cff
    .word $82ff
    .word $f2ff
    .word $e6ff
    .word $ceff
    .word $9eff
    .word $82ff
    .word $7cff
pointer_right:
    .word $00ff
    .word $00ff
    .word $60ff
    .word $30ff
    .word $18ff
    .word $30ff
    .word $60ff
    .word $00ff
pointer_left:
    .word $00ff
    .word $00ff
    .word $0cff
    .word $18ff
    .word $30ff
    .word $18ff
    .word $0cff
    .word $00ff
zero: .byte 0
.segment "MAXGAME"
maxgame:
    .word 4
.segment "FNLIST"
filenames:
    .byte "00",0,0
    .byte "01",0,0
    .byte "02",0,0
    .byte "03",0,0
    .byte "04",0,0

.segment "BANK1"
games:
    .word $00,$00,$4a,$00,$50,$4a,$56,$4e,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$4a,$55,$5c,$58,$00,$4a,$00,$50,$4a,$56,$4e,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$4a,$57,$58,$5d,$51,$4e,$5b,$00,$50,$4a,$56,$4e,$6a,$6a
    .word $6a,$6a,$6a,$6a,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$52,$5d,$65,$5c,$00,$4a,$00,$50,$4a,$56,$4e,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$5b,$4e,$4a,$55,$55,$62,$00,$4c,$58,$58,$55,$00,$50,$4a
    .word $56,$4e,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .word $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .byte "this is bank1"
