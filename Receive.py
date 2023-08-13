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
import random
import argparse
import time
import os

def gen_packet (seqNum,pktLen):
    seqBytes = seqNum.to_bytes(4, byteorder = 'little')
    data = os.urandom(pktLen-4)
    return seqBytes+data

def getSeqNum (pkt):
    sequenceNum = int.from_bytes(pkt[0:4], byteorder = 'little')
    return sequenceNum


def main():
    parser = argparse.ArgumentParser(description='Go-back-N reliable transmission protocol')
    parser.add_argument('-d','--debug', help='Turn ON Debug Mode(OFF if -d flag not present)' ,action='store_true')
    parser.add_argument('-p','--port', type=int, help="Receiver's Port Number, integer", required=True)
    parser.add_argument('-n','--maxPkts', type=int, help='MAX_PACKETS, integer', required=True)
    parser.add_argument('-e','--pktErrRate', type=float, help='Packet Error Rate (RANDOM_DROP_PROB), float', required=True)
    args = vars(parser.parse_args())

    localIP     = "localhost"
    localPort   = 12014
    localPort = args['port']

    bufferSize  = 2048
    debugbit = args['debug']
    # Create a datagram socket
    recsock = socket(AF_INET, SOCK_DGRAM)

    # Bind to address and ip
    recsock.bind((localIP, localPort))

    maxPkts = 100
    maxPkts = args['maxPkts']

    randomDropProb = 0.2
    randomDropProb = args['pktErrRate']

    nextFrameExpected = 0 # represents cummulative ack to be sent for packets being dropped

    # Listen for incoming datagrams
    while True:
        data, addr = recsock.recvfrom(2048) # buffer size is 2048 bytes
        seq_num = getSeqNum(data)
        if randomDropProb > 0.9:
            break
        if random.uniform(0,1) < randomDropProb and seq_num != 0:
            continue
        
        if seq_num == nextFrameExpected:
            ackPkt = gen_packet(seq_num,4)
            if debugbit:
                print(f"Seq #:{seq_num%255} Time Received: {time.time()} Packet dropped: false")
            recsock.sendto(ackPkt, addr)
            nextFrameExpected += 1
            # nextFrameExpected %= 255
            if nextFrameExpected == maxPkts:
                break
        else :
            sent_seq_num = nextFrameExpected - 1
            if debugbit:
                print(f"Seq #:{seq_num%255} Time Received: {time.time()} Packet dropped: true")
            if sent_seq_num >= 0:
                ackPkt = gen_packet(sent_seq_num,4)
                recsock.sendto(ackPkt, addr)

    print(f"Random Probability for dropping {randomDropProb}")
    print("Receiver terminated")
    recsock.close()

if __name__ == "__main__":
    main()

