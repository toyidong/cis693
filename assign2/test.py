#!/usr/bin/env python

import rospy
from turtlesim.msg import *
from turtlesim.srv import *
from geometry_msgs.msg import Twist
from std_srvs.srv import *
import random
from math import atan2,pi, sqrt, pow
import sys


tolerance = 1 #The distance until we say the hunter finds the hunted.

#Gets the Hunter's Pose, this is a subscriber call back
def hunterPose(data):
    global turtle1x, turtle1y, turtle1theta
    turtle1x = data.x
    turtle1y = data.y
    turtle1theta = data.theta

#Gets the Hunted's Pose, this is a subscriber call back
def runnerPose(data):
    global turtleTargetx, turtleTargety, turtleTargettheta
    turtleTargetx = data.x
    turtleTargety = data.y
    turtleTargettheta = data.theta

#Create a new Turtle to Hunt
def spawnNewTurtle():
    global turtleTargetx, turtleTargety, turtleTargettheta
    random.seed()
    turtleTargetx = random.randint(1, 10)
    turtleTargety = random.randint(1, 10)
    turtleTargettheta = random.randint(0,6)
    spawnTurtle(turtleTargetx,turtleTargety,turtleTargettheta,"turtleTarget")

def move_runner():
    global start, now
    random.seed()
    vel_msg = Twist()
    #Porportional controller
    #linear velocity in the x-axis
    vel_msg.linear.x = 1.0
    vel_msg.linear.y = 0
    vel_msg.linear.z = 0
    #angular velocity in the z-axis
    vel_msg.angular.x = 0
    vel_msg.angular.y = 0
    now = rospy.Time.now().nsecs
    d = now - start
    # turn target turtle every 2 seconds
    if not(d%2):
        # the angular value for target turtle is [-1, 1]
        vel_msg.angular.z = random.randint(-1,1) * random.random()
    else:
        # keep direction unchanged for target turtle
        vel_msg.angular.z = 0
    #publishing our vel_msg
    velocity_publisher_runner.publish(vel_msg)

    rospy.sleep(1)

#After finding a turtle, reset the stage for the next turtle
def resetHunt():
    try:
        killTurtle("turtleTarget")
    except:
        pass
    clearStage()
    spawnNewTurtle()

#Get the distance between two points on a plane.
def getDistance(x1, y1, x2, y2):
    return sqrt(pow((x2-x1),2) + pow((y2-y1),2))


def hunting_method():
    global motion
    distance = getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
    y = turtleTargety - turtle1y
    x = turtleTargetx - turtle1x

    motion.linear.x = 1.
    Theta = atan2(y, x) 
    
    # absolute summation greater than pi, 
    # need to compare y coordinates to get sign(+ or -)
    if (abs(Theta) + abs(turtle1theta) > pi):
        change = 1
        if turtleTargety > turtle1y :
            change = -1 
        motion.angular.z = change*(2*pi - (abs(Theta) + abs(turtle1theta)))
    # else if the orientation is almost precise, 
    # do not change angular until angular difference greater than 0.2
    elif (abs(Theta - turtle1theta) < 0.2):
        motion.angular.z = 0
    # else, set hunter angular.z
    else:
        motion.angular.z =  (Theta - turtle1theta) 
    pub.publish(motion)

#Main Function, sets up first hunt then loops.
def hunt():
    global turtle1x, turtle1y, turtleTargetx, turtleTargety

    #Set up board for first hunt.
    resetHunt()

    #Main Loop
    while not rospy.is_shutdown():
        rate.sleep()
        move_runner()
        #See how far away hunter is from hunted
        distance = getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
        #If <= tolerance then it is found
        if (distance <= tolerance):
            resetHunt()
        else: 
            hunting_method()
        rospy.sleep(0.01)

#Entry Point, sets up the ROS globals then calls hunt()
if __name__ == '__main__':
    try:
        global pub, rate, motion, start, now
        rospy.init_node('turtleHunt', anonymous=True)
        pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size = 10)
        velocity_publisher_runner = rospy.Publisher('/turtleTarget/cmd_vel', Twist, queue_size=10)
        rospy.Subscriber("/turtle1/pose", Pose, hunterPose) #Getting the hunter's Pose
        pose_subscriber_runner = rospy.Subscriber("/turtleTarget/pose", Pose, runnerPose) #Getting the hunted's Pose
        rate = rospy.Rate(5) #The rate of our publishing
        clearStage = rospy.ServiceProxy('/clear', Empty) #Blanks the Stage
        spawnTurtle = rospy.ServiceProxy('/spawn', Spawn) #Can spawn a turtle
        killTurtle = rospy.ServiceProxy('/kill', Kill) #Delets a turtle
        motion = Twist() #The variable we send out to publish
        # timestamp for 2 second interval publish
        start = rospy.Time.now().nsecs
        now = rospy.Time.now().nsecs

        hunt()

    except rospy.ROSInterruptException:
        pass