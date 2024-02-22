; This gcode is generated by my specialised python script for my PCB manufacturer project :))

; Machine Initialization Sequence...

G21 ; to set metric units
G90 ; to set absolute mode , G91 for incremental mode
G94 ; To set the active feed rate mode to units per minute mode

M5 ; disabling spindle PWM
C0 ; Choosing the empty tool slot in the multiplexer circuits

B1 ; Turn ON Machine

$H ; Homing :)
G10 P0 L20 X0.0Y0.0Z0.0 ; Force Reset current coordinates after homing


; The following gcode is the PCB holes drill gcode

; Getting and Activating Tool-2, The Tool.Spindle
G00X165.0Y91.0Z12.0 ; Go to Tool-2 Home Pos
G00X188 ; Enter Female Kinematic Mount Home Pos
A1 ; Latch on Kinematic Mount
G4 P5 ; Wait for Kinematic Mount to fully attach
G00X92 ; Exit Female Kinematic Mount Home Pos
#TODO X0.0Y0.0Z0.0 ;  ;Add tool offset coordinate
C2 ; Choosing tool 2 in the choose demultiplexer circuits

F600 ; setting default feedrate

S255 ; sets pwm speed when we enable it

G01 Z10F20 ; Moving Spindle to UP Postion

M3 ; Turn Motor ON
G4 P2 ; dwell for 2 seconds so motor reaches full RPM

G01 X31.36Y88.51F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y85.97F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y83.43F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y77.08F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y74.54F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y72.0F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y65.65F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y63.11F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y60.57F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y60.57F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y63.11F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y65.65F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y72.0F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y74.54F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y77.08F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y83.43F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y85.97F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y88.51F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y88.51F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y77.08F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y65.65F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y83.43F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y72.0F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y60.57F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y54.22F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y51.68F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y49.14F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y42.79F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y40.25F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y37.71F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y31.36F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y28.82F600
G01 Z13F1
G01 Z10F20
G01 X31.36Y26.28F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y26.28F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y28.82F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y31.36F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y37.71F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y40.25F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y42.79F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y49.14F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y51.68F600
G01 Z13F1
G01 Z10F20
G01 X50.41Y54.22F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y54.22F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y42.79F600
G01 Z13F1
G01 Z10F20
G01 X33.9Y31.36F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y49.14F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y37.71F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y26.28F600
G01 Z13F1
G01 Z10F20
G01 X61.205Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X58.665Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X56.125Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X53.585Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X51.045Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X48.505Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X45.965Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X43.425Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X40.885Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X38.345Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X35.805Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X33.265Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X30.725Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X28.185Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X25.645Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X23.105Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X20.565Y129.15F600
G01 Z13F1
G01 Z10F20
G01 X40.885Y83.43F600
G01 Z13F1
G01 Z10F20
G01 X69.46Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X69.46Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X66.285Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X66.285Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y54.22F600
G01 Z13F1
G01 Z10F20
G01 X63.11Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X63.11Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X54.855Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X54.855Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X51.68Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X51.68Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X58.03Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X58.03Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X44.695Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X44.695Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X41.52Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X41.52Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X33.265Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X33.265Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X30.09Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X30.09Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X36.44Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X36.44Y108.195F600
G01 Z13F1
G01 Z10F20
G01 X25.645Y105.02F600
G01 Z13F1
G01 Z10F20
G01 X23.105Y105.02F600
G01 Z13F1
G01 Z10F20
G01 X20.565Y105.02F600
G01 Z13F1
G01 Z10F20
G01 X23.105Y99.305F600
G01 Z13F1
G01 Z10F20
G01 X25.645Y99.305F600
G01 Z13F1
G01 Z10F20
G01 X73.27Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X75.81Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X16.12Y98.035F600
G01 Z13F1
G01 Z10F20
G01 X16.12Y100.575F600
G01 Z13F1
G01 Z10F20
G01 X18.025Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X12.945Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X9.135Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X9.135Y105.655F600
G01 Z13F1
G01 Z10F20
G01 X12.31Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X12.31Y105.655F600
G01 Z13F1
G01 Z10F20
G01 X15.485Y105.655F600
G01 Z13F1
G01 Z10F20
G01 X15.485Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X5.96Y105.655F600
G01 Z13F1
G01 Z10F20
G01 X5.96Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X30.725Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X20.565Y115.815F600
G01 Z13F1
G01 Z10F20
G01 X14.215Y125.34F600
G01 Z13F1
G01 Z10F20
G01 X11.675Y125.34F600
G01 Z13F1
G01 Z10F20
G01 X9.135Y125.34F600
G01 Z13F1
G01 Z10F20
G01 X30.725Y121.53F600
G01 Z13F1
G01 Z10F20
G01 X25.645Y121.53F600
G01 Z13F1
G01 Z10F20
G01 X16.12Y120.895F600
G01 Z13F1
G01 Z10F20
G01 X5.96Y120.895F600
G01 Z13F1
G01 Z10F20
G01 X20.565Y121.53F600
G01 Z13F1
G01 Z10F20
G01 X20.565Y124.07F600
G01 Z13F1
G01 Z10F20
G01 X65.65Y125.975F600
G01 Z13F1
G01 Z10F20
G01 X75.81Y125.975F600
G01 Z13F1
G01 Z10F20
G01 X75.81Y120.26F600
G01 Z13F1
G01 Z10F20
G01 X75.81Y117.72F600
G01 Z13F1
G01 Z10F20
G01 X75.81Y115.18F600
G01 Z13F1
G01 Z10F20
G01 X40.885Y60.57F600
G01 Z13F1
G01 Z10F20
G01 X40.885Y68.19F600
G01 Z13F1
G01 Z10F20
G01 X75.6Y131.8F600
G01 Z13F1
G01 Z10F20
G01 X6.6Y131.8F600
G01 Z13F1
G01 Z10F20
G01 X6.6Y6.3F600
G01 Z13F1
G01 Z10F20
G01 X75.6Y6.3F600
G01 Z13F1
G01 Z10F20
G01 X66.285Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X74.27Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X28.82Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X38.345Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X47.87Y14.215F600
G01 Z13F1
G01 Z10F20
G01 X57.395Y14.215F600
G01 Z13F1
G01 Z10F20

M5 ; disabling spindle PWM

; Returning the Deactivating Tool-2
C0 ; PWM Tool select demultiplexer to select tool zero which is the empty tool slot in multiplexers
#TODO X-0.0Y-0.0Z-0.0 ;  ;Remove tool offset coordinate
G00X165.0Y91.0Z12.0 ; Go to Tool-2 Home Pos
G00X92 ; Enter Female Kinematic Mount Home Pos
A0 ; Latch OFF Kinematic Mount
G4 P5 ; Wait for Kinematic Mount to fully detach
G00X188 ; Exit Female Kinematic Mount Home Pos

; Machine deinitialization Sequence... 
G00X0.0Y0.0Z0.0
B0 ; Turn Machine OFF
