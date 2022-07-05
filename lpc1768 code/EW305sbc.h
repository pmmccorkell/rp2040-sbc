/* C Library for the WRC-305-SBC
 J Bradshaw
 L DeVries
 20140912
 20140918 J Bradshaw - Found CS mistake in Encoder routines
    Added comments in Init function, encoder functions
 20150210 J Bradshaw - Initialized DigitalOuts with pre-defined logic
   levels (CS's high, etc)
 20161011 J Bradshaw - Changed MAX1270 ADC SCLK to 5MHz and format(12, 0)
   for conversion mode to match datasheet (200ns SCLK max PW high and low)
 20190814 L DeVries - revised mbedWSEsbc to create EW305-specific library
*/
#ifndef TACH_H
#define TACH_H




/**
 * Includes
 */
#include "mbed.h"

// LS7366 ENCODER IC DEFINITIONS
//=============================================================================
// Four commands for the Instruction Register (B7,B6) - LS7366
//=============================================================================
#define CLR     0x00    //Clear Instruction
#define RD      0x01    //Read Instruction
#define WR      0x02    //Write Instruction
#define LOAD    0x03    //Load Instruction

//=============================================================================
// Register to Select from the Instruction Register (B5,B4,B3) - LS7366
//=============================================================================
#define NONE        0x00    //No Register Selected
#define MDR0        0x01    //Mode Register 0
#define MDR1        0x02    //Mode Register 1
#define DTR         0x03    //Data Transfer Register
#define CNTR        0x04    //Software Configurable Counter Register
#define OTR         0x05    //Output Transfer Register
#define STR         0x06    //Status Register
#define NONE_REG    0x07    //No Register Selected


//=============================================================================
// AD5293 Command Set - Table 11 of Datasheet Command Operation Truth Table
//=============================================================================
#define MAX_SCALE 0.9f
#define NOP 0x0   // Do nothing
#define WRDAC 0x1 // Write the contects of the serial register to the RDAC (D9 - D0)
#define RRDAC 0x2 // Read the RDAC wiper setting from SDO in the next frame
#define RESET 0x4 // Refresh the RDAC with midscale code
#define WCON 0x6  // Write contents of serial reg to control reg (D2, D1)
#define RCON 0x7  // Read control register from SDO output in the next frame
#define PWDN 0x8  // Software power down (D0=0 normal mode, D0=1 shutdown mode)


/**
 * Tach and motor control Interface.
 */
class EW305sbc
{

public:

    /**
     * Constructor.
     *
     * Tracks encoder position and speed, provides
     * rotations per second (Hz) output
     *
     * @param Channel input channel from SPI chip.
     * @param pulsesPerRev Number of pulses in one revolution (quadrature encoder).
     */
    EW305sbc(int ch, int pulsesPerRev);

    /**
     * Read the speed of the motor shaft
     */
    float getSpeed(void);
    
    /**
     * Read the speed of the motor shaft
     */
    int getCount(void);
    
    /**
     * Read angle of the motor shaft
     */
    float getAngle(void);
     
    /**
     * Read the state of the motor shaft
     */
    long LS7366_read_counter(int chan_num);
    
    /**
     * Read the state of the motor shaft, quadrature??
     */
    void LS7366_quad_mode_x4(int chan_num);
    
    /**
     * Reset the encoder counts
     */
    void LS7366_reset_counter(int chan_num);
    
    /**
     * set input voltage to motor
     */
    void analog_input(float inp);
    
    /**
     * initialize digital potentiometer
     */
    void init_ad5293(void);
    void reset_ad5293(void);
    
private:

    // Set-up hardwired IO
    Ticker updater;
    
    int          ch_;
    int          pulsesPerRev_;
    
    
    //SPI spi_max1270(PinName p5,PinName p6,PinName p7);
    SPI spi;//(PinName p5,PinName p6,PinName p7);
    DigitalOut ls7166_cs1;//(PinName p19,int tmp=1); //CS for LS7366-1 (U8)
    DigitalOut ls7166_cs2;//(PinName p20, int tmp=1); //CS for LS7366-2 (U9)
    DigitalOut ad5293_sync; // (p12,1); //CS for Digital potentiometer AD5293
    DigitalIn ad5293_rdy; // (p27); // data ready input pin from AD5293 digital pot
    
    long         count_;
    float        speed_;
    float        angle_;
    long         countp_;
    int          dt_;
    
    /**
     * internal encoder cmd
     */
    void LS7366_cmd(int inst,  int reg);
    
    /**
     * write to DTR pin?
     */
    void LS7366_write_DTR(int chan_num,long enc_value);
    
    /**
     * initialization
     */
    void init();
    
    
    /**
     * update current speed estimate
     */
    void recalc(void);
    
    /**
     * write data to digital potentiometer
     */
    void write_ad5293(int cmd, int data);
    
    
};

#endif /* TACH_H */