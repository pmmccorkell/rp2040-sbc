//#include "mbed.h"
#include "EW305sbc.h"


EW305sbc::EW305sbc(int ch, int pulsesPerRev) 
    : ch_(ch), pulsesPerRev_(pulsesPerRev), spi(p5, p6, p7), ls7166_cs1(p19,1), ls7166_cs2(p20,1), ad5293_sync(p12,1), ad5293_rdy(p27)
{
    init();
}

void EW305sbc::init()
{
    dt_ = 0.001; // 500 Hz, also must update lines 19 and 38 since dt_ is not working for some reason??
    speed_ = 0.0; // initial distance
    countp_ = 0;
    count_ = 0;
    angle_ = 0.0;
    /** configure the rising edge to start the timer */
    updater.attach(callback(this, &EW305sbc::recalc), 0.001); // 125 Hz, syntax from https://os.mbed.com/forum/mbed/topic/1964/?page=1
    wait(.2);   //delay at beginning for voltage settle purposes

    // initialize channel ch_ encoder by 
    LS7366_reset_counter(ch_);
    LS7366_quad_mode_x4(ch_);
    LS7366_write_DTR(ch_,0);
}


void EW305sbc::recalc()
{
    // Read encoder
    count_ = LS7366_read_counter(ch_); // input is the encoder channel
    
    // convert count to angle
    angle_ = count_*2.0*3.14159/(4.0*pulsesPerRev_);
    
    // Estimate speed (counts/sec)
    speed_ = -(count_-countp_)/0.001*2.0*3.14159/(4.0*pulsesPerRev_);

    // Age variable
    countp_ = count_;
}


int EW305sbc::getCount(void)
{
    return count_;
}

float EW305sbc::getSpeed(void)
{
    return speed_;
}

float EW305sbc::getAngle(void)
{
    return angle_;
}


//---- Function Listing -------------------------------

//----- LS7366 Encoder/Counter Routines --------------------
void EW305sbc::LS7366_cmd(int inst,  int reg)
{
    char cmd;
    spi.format(8, 0);
    spi.frequency(2000000);
    cmd = (inst << 6) | (reg << 3);
//    printf("\r\ncmd=0X%2X", cmd);
    spi.write(cmd);
}

long EW305sbc::LS7366_read_counter(int chan_num)
{
    union bytes {
        char byte_enc[4];
        long long_enc;
    } counter;

    counter.long_enc = 0;
    spi.format(8, 0);
    spi.frequency(2000000);

    if(chan_num!=2) {
        ls7166_cs1 = 0;
        wait_us(1);
        LS7366_cmd(LOAD,OTR);//cmd = 0xe8, LOAD to OTR
        ls7166_cs1 = 1;
        wait_us(1);
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
        wait_us(1);
        LS7366_cmd(LOAD,OTR);//cmd = 0xe8, LOAD to OTR
        ls7166_cs2 = 1;
        wait_us(1);
        ls7166_cs2 = 0;
    }
    wait_us(1);
    LS7366_cmd(RD,CNTR);  //cmd = 0x60, READ from CNTR
    counter.byte_enc[3] = spi.write(0x00);
    counter.byte_enc[2] = spi.write(0x00);
    counter.byte_enc[1] = spi.write(0x00);
    counter.byte_enc[0] = spi.write(0x00);

    if(chan_num!=2) {
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }

    return counter.long_enc;  //return count
}

void EW305sbc::LS7366_quad_mode_x4(int chan_num)
{

    spi.format(8, 0);
    spi.frequency(2000000);

    if(chan_num!=2) {
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
    }
    wait_us(1);
    LS7366_cmd(WR,MDR0);// Write to the MDR0 register
    wait_us(1);
    spi.write(0x03); // X4 quadrature count mode
    if(chan_num!=2) {
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }
}

void EW305sbc::LS7366_reset_counter(int chan_num)
{
    spi.format(8, 0);           // set up SPI for 8 data bits, mode 0
    spi.frequency(2000000);     // 2MHz SPI clock

    if(chan_num!=2) {           // activate chip select
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
    }
    wait_us(1);                 // short delay
    LS7366_cmd(CLR,CNTR);       // Clear the counter register
    if(chan_num!=2) {           // de-activate chip select
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }
    wait_us(1);                 // short delay

    if(chan_num!=2) {           // activate chip select
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
    }
    wait_us(1);                 // short delay
    LS7366_cmd(LOAD,CNTR);      // load counter reg
    if(chan_num!=2) {           // de-activate chip select
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }
}

void EW305sbc::LS7366_write_DTR(int chan_num, long enc_value)
{
    union bytes {              // Union to speed up byte writes
        char byte_enc[4];
        long long_enc;
    } counter;

    spi.format(8, 0);           // set up SPI for 8 data bits, mode 0
    spi.frequency(2000000);     // 2MHz SPI clock

    counter.long_enc = enc_value; // pass enc_value to Union

    if(chan_num!=2) {             // activate chip select
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
    }
    wait_us(1);                 // short delay
    LS7366_cmd(WR,DTR);         // Write to the Data Transfer Register
    spi.write(counter.byte_enc[3]); // Write the 32-bit encoder value
    spi.write(counter.byte_enc[2]);
    spi.write(counter.byte_enc[1]);
    spi.write(counter.byte_enc[0]);
    if(chan_num!=2) {           // de-activate the chip select
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }

    wait_us(1);                 // short delay
    if(chan_num!=2) {           // activate chip select
        ls7166_cs1 = 0;
    } else {
        ls7166_cs2 = 0;
    }
    wait_us(1);                 // short delay
    LS7366_cmd(LOAD,CNTR);      // load command to the counter register from DTR
    if(chan_num!=2) {           // de-activate chip select
        ls7166_cs1 = 1;
    } else {
        ls7166_cs2 = 1;
    }
}

// Write command and data - cmd[B13:B10], Data[B9:B0]
void EW305sbc::write_ad5293(int cmd, int data)
{
    spi.frequency(10000000); // Datasheet states up to 50MHz operation
    spi.format(16, 1);       // 16 data bits, CPOL0, and CPHA1 (datasheet page 8)
    uint16_t dataw = (cmd << 10) | data;  // set data write bits (command and data)
    ad5293_sync = 0;
    spi.write(dataw); // SPI transmit of 16 bits

    int timeout = 0;
    while(!ad5293_rdy) { // takes about 250ns to update
        timeout++;
        if(timeout >1000) {
            //pc.printf("Timeout waiting for RDY wiper update! timout=%d\r\n\r\n", timeout);
            wait(2);
        }
    }
    ad5293_sync =1;
    spi.format(8,0);// return to 'normal' SPI format
}


//Motor control routine for digital potentiometer analog driver board
// inp is analog voltage output (+/-1.0)
void EW305sbc::analog_input(float inp)
{
    if(inp>MAX_SCALE)
        inp=MAX_SCALE;
    if(inp<-MAX_SCALE)
        inp=-MAX_SCALE;
    
    write_ad5293(WCON,0x3FF); // Write to Control Register, C2=1 (normal mode), C1=1 (allows update of wiper)
    write_ad5293(WRDAC,512 + inp*512);
}

void EW305sbc::reset_ad5293()
{
    write_ad5293(RESET,0x3FF);
    wait(2.5);
    LS7366_reset_counter(1);
    LS7366_quad_mode_x4(1);
    LS7366_write_DTR(1,0);
}

void EW305sbc::init_ad5293()
{
    write_ad5293(WCON,0x3FF); // Write to Control Register, C2=1 (normal mode), C1=1 (allows update of wiper)
    write_ad5293(RESET,0x3FF);
    wait(.4);    // allow time for motor to settle if the mbed was just reset while motor was moving
    LS7366_reset_counter(1);
    LS7366_quad_mode_x4(1);
    LS7366_write_DTR(1,0);

    write_ad5293(WCON,0x3FF);   // Write to Control Register, C2=1 (normal mode), C1=1 (allows update of wiper)
    wait(1);
}