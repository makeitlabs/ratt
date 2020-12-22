EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 3 3
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L uratt:ER-TFT0.96-1 LCD?
U 1 1 62F12C4B
P 5800 2300
AR Path="/62F12C4B" Ref="LCD?"  Part="1" 
AR Path="/62EF036B/62F12C4B" Ref="LCD1"  Part="1" 
F 0 "LCD1" H 5800 2250 50  0000 L CNN
F 1 "ER-TFT0.96-1" H 8600 800 50  0000 L CNN
F 2 "uratt:ER-TFT0.96-1" H 5750 2375 50  0001 C CNN
F 3 "https://www.buydisplay.com/download/manual/ER-TFT0.96-1_Datasheet.pdf" H 5750 2375 50  0001 C CNN
	1    5800 2300
	1    0    0    -1  
$EndComp
NoConn ~ 5700 3700
Wire Wire Line
	5700 3000 5450 3000
$Comp
L Device:C_Small C?
U 1 1 62F12C53
P 6150 2000
AR Path="/62F12C53" Ref="C?"  Part="1" 
AR Path="/62EF036B/62F12C53" Ref="C34"  Part="1" 
F 0 "C34" H 6242 2046 50  0000 L CNN
F 1 "0.1uF" H 6242 1955 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 6150 2000 50  0001 C CNN
F 3 "~" H 6150 2000 50  0001 C CNN
	1    6150 2000
	1    0    0    -1  
$EndComp
Wire Wire Line
	6150 1900 6150 1850
$Comp
L Device:C_Small C?
U 1 1 62F12C5A
P 5750 2000
AR Path="/62F12C5A" Ref="C?"  Part="1" 
AR Path="/62EF036B/62F12C5A" Ref="C33"  Part="1" 
F 0 "C33" H 5842 2046 50  0000 L CNN
F 1 "1uF" H 5842 1955 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 5750 2000 50  0001 C CNN
F 3 "~" H 5750 2000 50  0001 C CNN
	1    5750 2000
	1    0    0    -1  
$EndComp
Wire Wire Line
	5750 1850 5750 1900
Wire Wire Line
	5750 2100 5750 2150
Wire Wire Line
	5750 2150 6150 2150
Wire Wire Line
	6150 2150 6150 2100
Connection ~ 5750 1850
Wire Wire Line
	5750 1850 6150 1850
Wire Wire Line
	5550 1850 5750 1850
Wire Wire Line
	5450 3000 5450 3850
$Comp
L Transistor_FET:BSS83P Q?
U 1 1 62F12C68
P 5050 2000
AR Path="/62F12C68" Ref="Q?"  Part="1" 
AR Path="/62EF036B/62F12C68" Ref="Q3"  Part="1" 
F 0 "Q3" H 4850 1900 50  0000 L CNN
F 1 "DMP31D0U" H 4650 1800 50  0000 L CNN
F 2 "Package_TO_SOT_SMD:SOT-23" H 5250 1925 50  0001 L CIN
F 3 "http://www.farnell.com/datasheets/1835997.pdf" H 5050 2000 50  0001 L CNN
	1    5050 2000
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small_US R?
U 1 1 62F12C6E
P 5150 2400
AR Path="/62F12C6E" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12C6E" Ref="R51"  Part="1" 
F 0 "R51" H 5218 2446 50  0000 L CNN
F 1 "220" H 5218 2355 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 5150 2400 50  0001 C CNN
F 3 "~" H 5150 2400 50  0001 C CNN
	1    5150 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	5700 2800 5550 2800
Connection ~ 5550 1850
Wire Wire Line
	5550 2800 5550 2700
Wire Wire Line
	5700 2700 5550 2700
Connection ~ 5550 2700
Wire Wire Line
	5550 2700 5550 1850
Wire Wire Line
	5450 2500 5700 2500
Connection ~ 5450 3000
Wire Wire Line
	5450 2500 5450 3000
Wire Wire Line
	5700 2600 5150 2600
Wire Wire Line
	5150 2600 5150 2500
Wire Wire Line
	5150 2300 5150 2200
Wire Wire Line
	5150 1800 5150 1750
Wire Wire Line
	5150 1750 5550 1750
Connection ~ 5550 1750
Wire Wire Line
	5550 1750 5550 1850
$Comp
L Device:R_Small_US R?
U 1 1 62F12C84
P 4750 1750
AR Path="/62F12C84" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12C84" Ref="R45"  Part="1" 
F 0 "R45" H 4818 1796 50  0000 L CNN
F 1 "10K" H 4818 1705 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 4750 1750 50  0001 C CNN
F 3 "~" H 4750 1750 50  0001 C CNN
	1    4750 1750
	1    0    0    -1  
$EndComp
Wire Wire Line
	4850 2000 4750 2000
Wire Wire Line
	4750 2000 4750 1850
Wire Wire Line
	4750 1650 4750 1550
Wire Wire Line
	4750 1550 5150 1550
Wire Wire Line
	5150 1550 5150 1750
Connection ~ 5150 1750
Connection ~ 4750 2000
NoConn ~ 5700 3600
Wire Wire Line
	5700 3500 5200 3500
Wire Wire Line
	5700 3100 5200 3100
Text Notes 8700 1500 0    50   ~ 0
GRAPHIC LCD
Text Notes 6700 2350 0    50   ~ 0
BACKLIGHT\nVF=3.2V IF=15mA\n
$Comp
L Device:R_Small_US R?
U 1 1 62F12C96
P 5000 2850
AR Path="/62F12C96" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12C96" Ref="R48"  Part="1" 
F 0 "R48" V 4900 2800 50  0000 L CNN
F 1 "47" V 5100 2800 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 5000 2850 50  0001 C CNN
F 3 "~" H 5000 2850 50  0001 C CNN
	1    5000 2850
	0    1    1    0   
$EndComp
$Comp
L Device:R_Small_US R?
U 1 1 62F12C9C
P 4850 3050
AR Path="/62F12C9C" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12C9C" Ref="R46"  Part="1" 
F 0 "R46" V 4750 3000 50  0000 L CNN
F 1 "47" V 4950 3000 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 4850 3050 50  0001 C CNN
F 3 "~" H 4850 3050 50  0001 C CNN
	1    4850 3050
	0    1    1    0   
$EndComp
$Comp
L Device:R_Small_US R?
U 1 1 62F12CA2
P 5000 3300
AR Path="/62F12CA2" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12CA2" Ref="R49"  Part="1" 
F 0 "R49" V 4900 3250 50  0000 L CNN
F 1 "47" V 5100 3250 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 5000 3300 50  0001 C CNN
F 3 "~" H 5000 3300 50  0001 C CNN
	1    5000 3300
	0    1    1    0   
$EndComp
$Comp
L Device:R_Small_US R?
U 1 1 62F12CA8
P 4850 3500
AR Path="/62F12CA8" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12CA8" Ref="R47"  Part="1" 
F 0 "R47" V 4750 3450 50  0000 L CNN
F 1 "47" V 4950 3450 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 4850 3500 50  0001 C CNN
F 3 "~" H 4850 3500 50  0001 C CNN
	1    4850 3500
	0    1    1    0   
$EndComp
$Comp
L Device:R_Small_US R?
U 1 1 62F12CAE
P 5000 3700
AR Path="/62F12CAE" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12CAE" Ref="R50"  Part="1" 
F 0 "R50" V 4900 3650 50  0000 L CNN
F 1 "47" V 5100 3650 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 5000 3700 50  0001 C CNN
F 3 "~" H 5000 3700 50  0001 C CNN
	1    5000 3700
	0    1    1    0   
$EndComp
Wire Wire Line
	5200 3100 5200 2850
Wire Wire Line
	5200 2850 5100 2850
Wire Wire Line
	5150 3200 5150 3050
Wire Wire Line
	5150 3050 4950 3050
Wire Wire Line
	5150 3200 5700 3200
Wire Wire Line
	5700 3300 5100 3300
Wire Wire Line
	5150 3400 5150 3500
Wire Wire Line
	5150 3500 4950 3500
Wire Wire Line
	5150 3400 5700 3400
Wire Wire Line
	5200 3500 5200 3700
Wire Wire Line
	5200 3700 5100 3700
Wire Wire Line
	4900 2850 4050 2850
$Comp
L Device:R_Small_US R?
U 1 1 62F12CC0
P 4350 2000
AR Path="/62F12CC0" Ref="R?"  Part="1" 
AR Path="/62EF036B/62F12CC0" Ref="R44"  Part="1" 
F 0 "R44" V 4250 1950 50  0000 L CNN
F 1 "1K" V 4450 1950 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 4350 2000 50  0001 C CNN
F 3 "~" H 4350 2000 50  0001 C CNN
	1    4350 2000
	0    1    1    0   
$EndComp
Wire Wire Line
	4250 2000 4050 2000
$Comp
L Connector_Generic:Conn_01x10 J?
U 1 1 62F12CC7
P 2900 2650
AR Path="/62F12CC7" Ref="J?"  Part="1" 
AR Path="/62EF036B/62F12CC7" Ref="J9"  Part="1" 
F 0 "J9" H 3000 3150 50  0000 C CNN
F 1 "Conn_01x10" H 3050 2050 50  0000 C CNN
F 2 "Connector_FFC-FPC:TE_1-1734839-0_1x10-1MP_P0.5mm_Horizontal" H 2900 2650 50  0001 C CNN
F 3 "~" H 2900 2650 50  0001 C CNN
	1    2900 2650
	-1   0    0    -1  
$EndComp
Wire Wire Line
	3100 2350 4050 2350
Wire Wire Line
	4050 2350 4050 2000
Wire Wire Line
	4050 2850 4050 2450
Wire Wire Line
	4050 2450 3100 2450
Wire Wire Line
	3100 2550 3950 2550
Wire Wire Line
	3950 2550 3950 3050
Wire Wire Line
	3850 3300 3850 2650
Wire Wire Line
	3850 2650 3100 2650
Wire Wire Line
	3750 3500 3750 2750
Wire Wire Line
	3750 2750 3100 2750
Wire Wire Line
	3650 3700 3650 2850
Wire Wire Line
	3650 2850 3100 2850
Wire Wire Line
	3100 2250 3950 2250
Wire Wire Line
	3950 2250 3950 1400
Wire Wire Line
	3950 1400 5550 1400
Wire Wire Line
	5550 1400 5550 1750
$Comp
L power:GND1 #PWR?
U 1 1 62F12CDD
P 3150 3500
AR Path="/62F12CDD" Ref="#PWR?"  Part="1" 
AR Path="/62EF036B/62F12CDD" Ref="#PWR091"  Part="1" 
F 0 "#PWR091" H 3150 3250 50  0001 C CNN
F 1 "GND1" H 3155 3327 50  0000 C CNN
F 2 "" H 3150 3500 50  0001 C CNN
F 3 "" H 3150 3500 50  0001 C CNN
	1    3150 3500
	1    0    0    -1  
$EndComp
Wire Wire Line
	3100 3150 3150 3150
Wire Wire Line
	3150 3150 3150 3500
$Comp
L power:GND1 #PWR?
U 1 1 62F12CE5
P 6150 2150
AR Path="/62F12CE5" Ref="#PWR?"  Part="1" 
AR Path="/62EF036B/62F12CE5" Ref="#PWR093"  Part="1" 
F 0 "#PWR093" H 6150 1900 50  0001 C CNN
F 1 "GND1" H 6155 1977 50  0000 C CNN
F 2 "" H 6150 2150 50  0001 C CNN
F 3 "" H 6150 2150 50  0001 C CNN
	1    6150 2150
	1    0    0    -1  
$EndComp
$Comp
L power:GND1 #PWR?
U 1 1 62F12CEB
P 5450 3850
AR Path="/62F12CEB" Ref="#PWR?"  Part="1" 
AR Path="/62EF036B/62F12CEB" Ref="#PWR092"  Part="1" 
F 0 "#PWR092" H 5450 3600 50  0001 C CNN
F 1 "GND1" H 5455 3677 50  0000 C CNN
F 2 "" H 5450 3850 50  0001 C CNN
F 3 "" H 5450 3850 50  0001 C CNN
	1    5450 3850
	1    0    0    -1  
$EndComp
Text Label 3200 2350 0    50   ~ 0
R_LCD_BL
Text Label 3200 2250 0    50   ~ 0
R_LCD_3.3V
Text Label 3200 2450 0    50   ~ 0
R_LCD_CS
Text Label 3200 2550 0    50   ~ 0
R_LCD_RESET
Text Label 3200 2650 0    50   ~ 0
R_LCD_DC
Text Label 3200 2750 0    50   ~ 0
R_LCD_CLK
Text Label 3200 2850 0    50   ~ 0
R_LCD_MOSI
Wire Wire Line
	4450 2000 4750 2000
Wire Wire Line
	3950 3050 4750 3050
Wire Wire Line
	3850 3300 4900 3300
Wire Wire Line
	3750 3500 4750 3500
Wire Wire Line
	3650 3700 4900 3700
Wire Wire Line
	3100 3050 3450 3050
Wire Wire Line
	3450 3050 3450 4650
Connection ~ 2950 4650
Wire Wire Line
	2950 4650 3050 4650
$Comp
L Device:R_Small_US R?
U 1 1 6319A3AD
P 3150 4650
AR Path="/6319A3AD" Ref="R?"  Part="1" 
AR Path="/62EF036B/6319A3AD" Ref="R43"  Part="1" 
F 0 "R43" V 3050 4600 50  0000 L CNN
F 1 "47" V 3250 4500 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3150 4650 50  0001 C CNN
F 3 "~" H 3150 4650 50  0001 C CNN
	1    3150 4650
	0    1    1    0   
$EndComp
Wire Wire Line
	2800 4800 2950 4800
Wire Wire Line
	2600 4800 2500 4800
Wire Wire Line
	2950 4650 2900 4650
Wire Wire Line
	2950 4800 2950 4650
Wire Wire Line
	2500 4800 2500 4650
$Comp
L Device:C_Small C?
U 1 1 6319A3BE
P 2700 4800
AR Path="/6319A3BE" Ref="C?"  Part="1" 
AR Path="/62EF036B/6319A3BE" Ref="C32"  Part="1" 
F 0 "C32" V 2800 4850 50  0000 L CNN
F 1 ".1uF" V 2900 4800 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 2700 4800 50  0001 C CNN
F 3 "~" H 2700 4800 50  0001 C CNN
	1    2700 4800
	0    1    1    0   
$EndComp
$Comp
L Switch:SW_Push SW?
U 1 1 6319A3C4
P 2700 4650
AR Path="/6319A3C4" Ref="SW?"  Part="1" 
AR Path="/62EF036B/6319A3C4" Ref="SW3"  Part="1" 
F 0 "SW3" H 2700 4935 50  0000 C CNN
F 1 "SW_Push" H 2700 4844 50  0000 C CNN
F 2 "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2" H 2700 4850 50  0001 C CNN
F 3 "~" H 2700 4850 50  0001 C CNN
	1    2700 4650
	1    0    0    -1  
$EndComp
$Comp
L power:GND1 #PWR?
U 1 1 6319ECB9
P 2500 4800
AR Path="/6319ECB9" Ref="#PWR?"  Part="1" 
AR Path="/62EF036B/6319ECB9" Ref="#PWR090"  Part="1" 
F 0 "#PWR090" H 2500 4550 50  0001 C CNN
F 1 "GND1" H 2505 4627 50  0000 C CNN
F 2 "" H 2500 4800 50  0001 C CNN
F 3 "" H 2500 4800 50  0001 C CNN
	1    2500 4800
	1    0    0    -1  
$EndComp
Connection ~ 2500 4800
Wire Wire Line
	3250 4650 3450 4650
Text Label 3200 3050 0    50   ~ 0
R_BTN
$Comp
L Device:Buzzer BZ?
U 1 1 60451D70
P 6400 5500
AR Path="/60451D70" Ref="BZ?"  Part="1" 
AR Path="/62EF036B/60451D70" Ref="BZ1"  Part="1" 
F 0 "BZ1" H 6552 5529 50  0000 L CNN
F 1 "Buzzer" H 6552 5438 50  0000 L CNN
F 2 "Buzzer_Beeper:Buzzer_CUI_CPT-9019S-SMT" V 6375 5600 50  0001 C CNN
F 3 "~" V 6375 5600 50  0001 C CNN
	1    6400 5500
	1    0    0    -1  
$EndComp
Wire Wire Line
	6300 5400 6200 5400
Wire Wire Line
	6200 5400 6200 5300
$Comp
L Transistor_FET:2N7002 Q?
U 1 1 60451D78
P 6100 6100
AR Path="/60451D78" Ref="Q?"  Part="1" 
AR Path="/62EF036B/60451D78" Ref="Q4"  Part="1" 
F 0 "Q4" H 6304 6146 50  0000 L CNN
F 1 "2N7002" H 6304 6055 50  0000 L CNN
F 2 "Package_TO_SOT_SMD:SOT-23" H 6300 6025 50  0001 L CIN
F 3 "https://www.onsemi.com/pub/Collateral/NDS7002A-D.PDF" H 6100 6100 50  0001 L CNN
	1    6100 6100
	1    0    0    -1  
$EndComp
Wire Wire Line
	6200 5900 6200 5800
Wire Wire Line
	6200 5600 6300 5600
$Comp
L Device:R_Small_US R?
U 1 1 60451D80
P 6200 5150
AR Path="/60451D80" Ref="R?"  Part="1" 
AR Path="/62EF036B/60451D80" Ref="R53"  Part="1" 
F 0 "R53" H 6268 5196 50  0000 L CNN
F 1 "100" H 6268 5105 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 6200 5150 50  0001 C CNN
F 3 "~" H 6200 5150 50  0001 C CNN
	1    6200 5150
	1    0    0    -1  
$EndComp
Wire Wire Line
	6200 6400 6200 6300
$Comp
L Device:R_Small_US R?
U 1 1 60451D8E
P 5650 6100
AR Path="/60451D8E" Ref="R?"  Part="1" 
AR Path="/62EF036B/60451D8E" Ref="R52"  Part="1" 
F 0 "R52" V 5550 6050 50  0000 L CNN
F 1 "1K" V 5750 6050 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 5650 6100 50  0001 C CNN
F 3 "~" H 5650 6100 50  0001 C CNN
	1    5650 6100
	0    1    1    0   
$EndComp
Wire Wire Line
	5750 6100 5900 6100
Wire Wire Line
	3100 2950 3550 2950
Wire Wire Line
	3550 2950 3550 4150
Wire Wire Line
	3550 4150 4900 4150
Wire Wire Line
	4900 4150 4900 6100
Wire Wire Line
	4900 6100 5550 6100
Text Label 3200 2950 0    50   ~ 0
R_BEEPER
Text Label 5700 4850 0    50   ~ 0
R_LCD_3.3V
Wire Wire Line
	6200 4850 5700 4850
Wire Wire Line
	6200 4850 6200 5050
Connection ~ 6150 2150
$Comp
L power:GND1 #PWR?
U 1 1 5FE7C0E9
P 6200 6400
AR Path="/5FE7C0E9" Ref="#PWR?"  Part="1" 
AR Path="/62EF036B/5FE7C0E9" Ref="#PWR094"  Part="1" 
F 0 "#PWR094" H 6200 6150 50  0001 C CNN
F 1 "GND1" H 6205 6227 50  0000 C CNN
F 2 "" H 6200 6400 50  0001 C CNN
F 3 "" H 6200 6400 50  0001 C CNN
	1    6200 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H?
U 1 1 5FEBDB85
P 8150 4550
AR Path="/61FC99B5/5FEBDB85" Ref="H?"  Part="1" 
AR Path="/62EF036B/5FEBDB85" Ref="H5"  Part="1" 
F 0 "H5" H 8250 4596 50  0000 L CNN
F 1 "MountingHole" H 8250 4505 50  0000 L CNN
F 2 "MountingHole:MountingHole_2.1mm" H 8150 4550 50  0001 C CNN
F 3 "~" H 8150 4550 50  0001 C CNN
	1    8150 4550
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H?
U 1 1 5FEBDB8B
P 8150 4800
AR Path="/61FC99B5/5FEBDB8B" Ref="H?"  Part="1" 
AR Path="/62EF036B/5FEBDB8B" Ref="H6"  Part="1" 
F 0 "H6" H 8250 4846 50  0000 L CNN
F 1 "MountingHole" H 8250 4755 50  0000 L CNN
F 2 "MountingHole:MountingHole_2.1mm" H 8150 4800 50  0001 C CNN
F 3 "~" H 8150 4800 50  0001 C CNN
	1    8150 4800
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H?
U 1 1 5FEBDB91
P 8150 5050
AR Path="/61FC99B5/5FEBDB91" Ref="H?"  Part="1" 
AR Path="/62EF036B/5FEBDB91" Ref="H7"  Part="1" 
F 0 "H7" H 8250 5096 50  0000 L CNN
F 1 "MountingHole" H 8250 5005 50  0000 L CNN
F 2 "MountingHole:MountingHole_2.1mm" H 8150 5050 50  0001 C CNN
F 3 "~" H 8150 5050 50  0001 C CNN
	1    8150 5050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H?
U 1 1 5FEBDB97
P 8150 5300
AR Path="/61FC99B5/5FEBDB97" Ref="H?"  Part="1" 
AR Path="/62EF036B/5FEBDB97" Ref="H8"  Part="1" 
F 0 "H8" H 8250 5346 50  0000 L CNN
F 1 "MountingHole" H 8250 5255 50  0000 L CNN
F 2 "MountingHole:MountingHole_2.1mm" H 8150 5300 50  0001 C CNN
F 3 "~" H 8150 5300 50  0001 C CNN
	1    8150 5300
	1    0    0    -1  
$EndComp
$Comp
L uratt:BREAKAWAY BK1
U 1 1 5FF4E008
P 1100 1050
F 0 "BK1" H 1473 1021 50  0000 L CNN
F 1 "BREAKAWAY" H 1473 930 50  0000 L CNN
F 2 "uratt:RATT_BITE" H 1100 1050 50  0001 C CNN
F 3 "" H 1100 1050 50  0001 C CNN
	1    1100 1050
	1    0    0    -1  
$EndComp
$Comp
L uratt:BREAKAWAY BK2
U 1 1 5FF4E66A
P 1100 1250
F 0 "BK2" H 1473 1221 50  0000 L CNN
F 1 "BREAKAWAY" H 1473 1130 50  0000 L CNN
F 2 "uratt:RATT_BITE" H 1100 1250 50  0001 C CNN
F 3 "" H 1100 1250 50  0001 C CNN
	1    1100 1250
	1    0    0    -1  
$EndComp
$Comp
L uratt:BREAKAWAY BK3
U 1 1 5FF50D6B
P 1100 1450
F 0 "BK3" H 1473 1421 50  0000 L CNN
F 1 "BREAKAWAY" H 1473 1330 50  0000 L CNN
F 2 "uratt:RATT_BITE" H 1100 1450 50  0001 C CNN
F 3 "" H 1100 1450 50  0001 C CNN
	1    1100 1450
	1    0    0    -1  
$EndComp
$Comp
L Device:Buzzer BZ?
U 1 1 5FF0EFC7
P 5750 5500
AR Path="/5FF0EFC7" Ref="BZ?"  Part="1" 
AR Path="/62EF036B/5FF0EFC7" Ref="BZ2"  Part="1" 
F 0 "BZ2" H 5902 5529 50  0000 L CNN
F 1 "Buzzer (ALT OPT)" H 5902 5438 50  0000 L CNN
F 2 "Buzzer_Beeper:Buzzer_CUI_CPT-9019S-SMT" V 5725 5600 50  0001 C CNN
F 3 "~" V 5725 5600 50  0001 C CNN
	1    5750 5500
	1    0    0    -1  
$EndComp
Wire Wire Line
	5650 5600 5600 5600
Wire Wire Line
	5600 5600 5600 5800
Wire Wire Line
	5600 5800 6200 5800
Connection ~ 6200 5800
Wire Wire Line
	6200 5800 6200 5600
Wire Wire Line
	5650 5400 5650 5300
Wire Wire Line
	5650 5300 6200 5300
Connection ~ 6200 5300
Wire Wire Line
	6200 5300 6200 5250
$EndSCHEMATC
