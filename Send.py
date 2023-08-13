# NAME: Sasubilli Yuvan
# Roll Number:CS20B070
# Course: CS3205 Jan. 2023 semester
# Lab number: 4
# Date of submission: April 5, 2023
# I confirm that the source file is entirely written by me without
# resorting to any dishonest means.
# Website(s) that I used for basic socket programming code are:
# URL(s): geeksforgeeks


from socket import *
import time
import os
import _thread
import argparse


class Timerclass(object):
    TIMER_STOP = -1

    def __init__(self):
        self._start_time = self.TIMER_STOP
        # self._duration = duration

    # Starts the timer
    def start(self):
        if self._start_time == self.TIMER_STOP:
            self._start_time = time.time()

    # Stops the timer
    def stop(self):
        if self._start_time != self.TIMER_STOP:
            self._start_time = self.TIMER_STOP

    # as mentioned timeout varies for sequence number 
    def timeout(self,seq_num,rtt_ave):
        if seq_num <= 10:
            timeout = 0.1 #100milliseconds in seconds
        else:
            timeout = 2 * rtt_ave
        return time.time() - self._start_time >= timeout
    
    # Determines whether the timer is runnning
    def running(self):
        return self._start_time != self.TIMER_STOP



# Shared resources across threads
baseNum = 0
mutex = _thread.allocate_lock()
send_timer = Timerclass()
start_time = {}

def gen_packet (seqNum,pktLen):
    seqBytes = seqNum.to_bytes(4, byteorder = 'little')
    data = os.urandom(pktLen-4)
    return seqBytes+data


# def packets_generator (pktGenrate,pktLen,maxPkts,buffer):
    

def send_packet(sock, packet, serverAddressPort):
    sock.sendto(packet, serverAddressPort)


def update_local_state_variables(sequence_number):
    global rtt_ave, num_packets_acknowledged,start_time

    # Calculate Round-trip-Time (RTT) for the packet
    rtt = time.time() - start_time[sequence_number]

    # Update average RTT (RTT_ave) for the packets acknowledged so far
    rtt_ave = (rtt_ave * num_packets_acknowledged + rtt) / (num_packets_acknowledged + 1)
    num_packets_acknowledged += 1
    return rtt


def getSeqNum (pkt):
    sequenceNum = int.from_bytes(pkt[0:4], byteorder = 'little')
    return sequenceNum

def receive(sock):
    global mutex
    global baseNum
    global send_timer
    global start_time
    global rtt_ave
    global num_retransmissions

    while True:
        ackPkt, addr = sock.recvfrom(2048)
        ack = getSeqNum(ackPkt)

        # If we get an ACK for the first in-flight packet
        
        if (ack >= baseNum):
            mutex.acquire()
            baseNum = ack + 1
            rtt = update_local_state_variables(ack)
            # time.sleep(0.001)
            # print(f"Seq #:{ack%255}  Time Generated:{start_time[ack]}  RTT:{rtt}   Number of Attempts:{(1+num_retransmissions[ack])}")
            # time.sleep(0.001)
            send_timer.stop()
            mutex.release()



def main():

    # Create a UDP socket at client side
    sendsock = socket(AF_INET, SOCK_DGRAM)

    global mutex
    global baseNum
    global send_timer
    global start_time
    global rtt_ave
    global num_packets_acknowledged
    global num_retransmissions
    global debugbit

    parser = argparse.ArgumentParser(description='Go-back-N reliable transmission protocol')
    parser.add_argument('-d','--debug', help='Turn ON Debug Mode(OFF if -d flag not present)' ,action='store_true')
    parser.add_argument('-s','--recName', help='Receiver Name or IP address., string', required=True)
    parser.add_argument('-p','--port', type=int, help="Receiver's Port Number, integer", required=True)
    parser.add_argument('-l','--pktLen', type=int, help='PACKET_LENGTH, in bytes, integer', required=True)
    parser.add_argument('-r','--pktGenRate', type=int, help='PACKET_GEN_RATE, in packets per second, integer', required=True)
    parser.add_argument('-n','--maxPkts', type=int, help='MAX_PACKETS, integer', required=True)
    parser.add_argument('-w','--winSize', type=int, help='WINDOW_SIZE, integer', required=True)
    parser.add_argument('-f','--maxBufSize', type=int, help='MAX_BUFFER_SIZE, integer', required=True)
    args = vars(parser.parse_args())

    # 8-bit sequence number field

    serverName = "localhost"
    serverName = args['recName']

    serverPort = 12014
    serverPort = args['port']

    serverAddressPort   = (serverName, serverPort)
    bufferSize          = 2048
    rtt_ave = 0
    # set packet length
    pktLength = 4
    pktLength = args['pktLen']

    # set packet Generation rate
    pktGenRate = 10
    pktGenRate = args['pktGenRate']

    # set maximum packets that can be sent
    maxPackets = 100
    maxPackets = args['maxPkts']

    # set window size
    windowSize = 4
    windowSize = args['winSize']

    # set maximum buffer size 
    maxBufferSize = 100
    maxBufferSize = args['maxBufSize']

    # create buffer for packets to be sent
    buffer = []


    debugbit =  args['debug']

    num_packets_acknowledged = 0
    num_retransmissions = {}
    # # start packet generator thread
    # generator_thread = threading.Thread(target=packets_generator, args=(pktGenRate,pktLength,maxPackets,buffer))
    # generator_thread.start()
    
    while 1:
        if len(buffer) >= maxPackets:
            break
        if len(buffer) < maxPackets:
            seqNum = (len(buffer))
            num_retransmissions[seqNum] = -1
            pkt = gen_packet(seqNum,pktLength)
            buffer.append(pkt)
        time.sleep((1/pktGenRate))

    nextToSend = 0

    # start the receiver thread now
    # mutex.acquire()
    _thread.start_new_thread(receive, (sendsock,))
    # mutex.release()
    loopbreak = False


    while True:
        mutex.acquire()
        if baseNum >= len(buffer):
            break

        # Send all the packets in the window
        while nextToSend < windowSize + baseNum:
            if nextToSend >= len(buffer):
                break

            print(f"Sending {nextToSend} sequence number packet")
            send_packet(sendsock, buffer[nextToSend], serverAddressPort)
            num_retransmissions[nextToSend] += 1
            if num_retransmissions[nextToSend] > 5:
                # print(f"The number of retransmissions of {nextToSend} pkt exceeded")
                # print(f"Total packets sent: {nextToSend}")
                # print(f"Total packets acknowledged: {num_packets_acknowledged}")
                # print(f"Retransmission Ratio: {num_packets_acknowledged/nextToSend}")
                # print(f"Average RTT: {rtt_ave}")
                loopbreak = True
                # break
            start_time[nextToSend] = time.time()
            nextToSend += 1


        if loopbreak:
            break

        # Start the timer
        if not send_timer.running():
            send_timer.start()
        
        while send_timer.running() and not send_timer.timeout(baseNum,rtt_ave):
            mutex.release()
            time.sleep(0.01)
            mutex.acquire()

        if send_timer.running() or send_timer.timeout(baseNum,rtt_ave):
            send_timer.stop()
            nextToSend = baseNum
        else:
            windowSize = min(windowSize, maxPackets - baseNum)
        mutex.release()
    
    total = 0
    for i in num_retransmissions:
        total += (1+num_retransmissions[i])

    print(f"Total packets sent: {nextToSend}")
    print(f"Total packets acknowledged: {num_packets_acknowledged}")
    if num_packets_acknowledged != 0:
        print(f"Retransmission Ratio: {total/num_packets_acknowledged}")
    print(f"Average RTT: {rtt_ave*1000}")
    sendsock.close()
        


if __name__ == "__main__":
    main()