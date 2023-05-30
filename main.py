# The main code for the platoon simulation
# Author: Xiong Xi, Haoran Su
# Email: xx719@nyu.edu, haoran.su@nyu.edu

# from __future__ import absolute_import
# from __future__ import print_function


import os
import subprocess
import sys

import optparse

import shutil
import random
import numpy as np
import time
import generate_seed as gs
import xml_time as xt
import generate_routefile as gr

# import matplotlib.pyplot as plt
# import xlsxwriter
# import bs4

base_path = '/Users/Administrator/Desktop/auto/auto2.0/'
save_path = base_path + 'results/'

# define the parameters we need
platoon_speed = 26.82  # set platoon operating speed
seed_num = 1  # set number of seed values
upper_sim_time = 3000  # set total simulation time
gap_range = [15.0]  # set the desired gap range车距
demand_range = range(9000, 9001)  # set total demand range
pla_len_range = range(10, 11)  # set the platoon length
pla_ratio_range = range(4, 5)  # set the platoon ratio, need to multply 0.1   γ
delta_range = range(0, 1)
pla_state = 'soft'  # set the platoon state, rigid or soft
GUI_state = 'sumo'  # set the option of choosing GUI
save_data_state = True  # set the option of saving travel time data

platoon_length = 2
platoon_ratio = 0.5
eta = 0.8  # platoon influence factor

# Road Segment parameters
road_length = 1000
Wrh = 10
capacity = 12000
delta = 0

bottleneck_light_jam_num = 20
bottleneck_heavy_jam_num = 30
vehicle_bottleneck_count = 0
#slowDown_flag = 0
if_car_has_slowed = {}
vid = None


def vehicle_pair(Leader_id, Follower_id, des_gap_v):
    traci.vehicle.setSpeedMode(Follower_id, 0)
    traci.vehicle.setLaneChangeMode(Follower_id, 512)

    Leader_pos = traci.vehicle.getPosition(Leader_id)
    # print(Leader_pos)
    Leader_speed = traci.vehicle.getSpeed(Leader_id)
    Follower_pos = traci.vehicle.getPosition(Follower_id)
    Follower_speed = traci.vehicle.getSpeed(Follower_id)

    pos_diff = Leader_pos[0] - Follower_pos[0]

    # car following model
    Follower_spd_set = Leader_speed + (pos_diff - des_gap_v) * 0.4

    traci.vehicle.setSpeed(Follower_id, Follower_spd_set)

    # Lane change model
    if Leader_pos[1] >= Follower_pos[1] + 0.03:
        traci.vehicle.changeSublane(Follower_id, 0.06)
    if Follower_pos[1] >= Leader_pos[1] + 0.03:
        traci.vehicle.changeSublane(Follower_id, -0.06)


def platoon(pla_list, pla_spd, des_gap, l_co, h_co, slowDown_flag):
    cur_pla_len = len(pla_list)
    if not slowDown_flag:
        traci.vehicle.setSpeed(pla_list[0], pla_spd)
    elif slowDown_flag:
        if pla_list[0] not in if_car_has_slowed and traci.vehicle.getPosition(pla_list[0])[0] < -1730:
            if slowDown_flag == 1:
                traci.vehicle.slowDown(pla_list[0], l_co * traci.vehicle.getSpeed(pla_list[0]), 30)
            elif slowDown_flag == 2:
                traci.vehicle.slowDown(pla_list[0], h_co * traci.vehicle.getSpeed(pla_list[0]), 30)

            if_car_has_slowed[pla_list[0]] = 1

    for i in range(cur_pla_len):

        if i < cur_pla_len and i > 0:
            vehicle_pair(pla_list[i - 1], pla_list[i], des_gap)


def get_platoon_list(pla_index):
    veh_list = traci.vehicle.getIDList()

    all_veh = []

    for item in veh_list:
        if item.split('_')[0] != 'Veh':
            all_veh.append(item)

    all_pla_list = []
    for i in range(len(pla_index)):
        pla_list_temp = []
        for item_v in all_veh:
            if int(item_v.split('_')[0]) == pla_index[i]:
                pla_list_temp.append(item_v)

        if len(pla_list_temp) > 0:
            pla_list_temp_num = []
            for item_v_num in pla_list_temp:
                pla_list_temp_num.append(int(item_v_num.split('_')[1]))

            pla_list_temp_num = sorted(pla_list_temp_num)

            pla_list_temp_final = []
            for item_v_final in pla_list_temp_num:
                pla_list_temp_final.append(str(pla_index[i]) + '_' + str(item_v_final))

            all_pla_list.append(pla_list_temp_final)

    # print(all_pla_list)
    return (all_pla_list)


# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
# else:
#     sys.exit("please set 'SUMO_HOME' variable in your shell")

from sumolib import checkBinary  # could be sumo or sumo-gui depending on os
import traci


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="simulate the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


def runner(l_co, h_co):  # coefficient of light congestion, coefficient of heavy congestion
    # begin the simulation
    for i in range(seed_num):  # choose multi seed values to get average results

        # choose random seed values
        seed = random.randint(2, 23423)
        # seed = 16042
        gs.random_experiment(seed)

        # Initialize the log for platoons and background traffic vehicles

        # leader_count_log = []
        # follower_count_log = []
        # background_count_log = []

        # number_platoon_controlled = 0
        first_controlled_platoon = []

        # iteration of parameters in the FQM model
        for platoon_ratio in pla_ratio_range:
            desired_gap = 15
            platoon_ratio *= 0.1
            for demand in demand_range:  # total vehicle demand
                for i_pla in pla_len_range:  # platoon length index
                    for delta in delta_range:  # platoon ratio index
                        # print(desired_gap, demand, i_pla, j_pla)

                        # determind real platoon length and ratio
                        platoon_length = i_pla  # calculate platoon length
                        # platoon_ratio = 0.5 # calculate platoon ratio
                        # generate the vehicle departure time and departure lane
                        platoon_index = gr.generate_routefile(upper_sim_time, demand, platoon_length, platoon_ratio,
                                                              seed, desired_gap, pla_state)
                        # generate the final SUMO file, include net file and vehicle file
                        traci.start([sumoBinary, '-c', os.path.join('data', 'hello.sumocfg')])

                        # initial counter and simulation values
                        counter = 0
                        stop_flag = 1
                        background_count_all = 0
                        platoon_count_all = 0
                        slowDown_flag = 0
                        # Initialize dict for speed and positions
                        platoon_speed_dict = {}
                        s = {}
                        name = None
                        # begin the SUMO simulation
                        while stop_flag:
                            cur_time = traci.simulation.getTime()  # get current simulation time
                            # if cur_time <= 1700:
                            # 	delta = 0
                            # elif cur_time <= 3600:
                            # 	delta = 2.1 + (cur_time-1700)/1900 * 2.1s'p
                            # else:
                            # 	delta = 4.2
                            # Initialize the counter for platoons and background traffic
                            background_count = 0
                            leader_count = 0
                            follower_count = 0
                            vehicle_bottleneck_count = 0

                            # set the limit of simulation time
                            if cur_time > upper_sim_time:
                                stop_flag = 0

                            platoon_speed = 16.67 + 10.15  # * (1 - cur_time/7200)

                            # start the traci command in SUMO
                            traci.simulationStep()

                            for veh_id in traci.vehicle.getIDList():
                                if (traci.vehicle.getPosition(veh_id)[0] > -1730 and traci.vehicle.getPosition(veh_id)[
                                    0] < -1530):
                                    vehicle_bottleneck_count += 1
                                if traci.vehicle.getTypeID(veh_id) == "Leader":
                                    s[veh_id] = traci.vehicle.getSpeed(veh_id)

                            platoon_num = []
                            if counter % 10 == 0:
                                for veh_id in traci.vehicle.getIDList():
                                    # print(veh_id + " speed: " + str(traci.vehicle.getSpeed(veh_id)))
                                    if traci.vehicle.getTypeID(veh_id) == "Leader":
                                        leader_count += 1
                                        platoon_num.append(veh_id)
                                    elif traci.vehicle.getTypeID(veh_id) == "Follower":
                                        follower_count += 1
                                    elif traci.vehicle.getTypeID(veh_id) == "Background":
                                        background_count += 1

                            if counter % 30 == 0:
                                if vehicle_bottleneck_count < bottleneck_light_jam_num:
                                    slowDown_flag = 0
                                elif vehicle_bottleneck_count >= bottleneck_heavy_jam_num:
                                    slowDown_flag = 2
                                else:
                                    slowDown_flag = 1


                            # control the vehicle action in a platoon
                            if pla_state == 'soft':
                                obtained_pla_list = get_platoon_list(
                                    platoon_index)
                                if obtained_pla_list:
                                    newest_platoon = obtained_pla_list[-1]
                                    index_platoon = newest_platoon[0].split("_")[0]
                                    # print("The latest platoon index is: " + index_platoon)
                                    if not platoon_speed_dict:
                                        platoon_speed_dict[index_platoon] = platoon_speed
                                    elif (index_platoon not in platoon_speed_dict) or (len(platoon_speed_dict) == 60):
                                        # if index_platoon == "0" and (len(platoon_speed_dict) == 60):
                                        # 	prev_platoon_index = "59"
                                        # else:
                                        prev_platoon_index = str(int(index_platoon) - 1)  # 倒数第二辆车

                                        if prev_platoon_index not in platoon_speed_dict:
                                            prev_platoon_index = list(platoon_speed_dict.items())[-1][0]
                                        prev_platoon_speed = platoon_speed_dict[prev_platoon_index]
                                        prev_platoon_str = prev_platoon_index + "_0"
                                        try:
                                            prev_platoon_pos = traci.vehicle.getPosition(prev_platoon_str)[0]
                                            # print("previous platoon position is:" + str(prev_platoon_pos))
                                            prev_platoon_residual_time = ((
                                                                              -1530) - prev_platoon_pos) / prev_platoon_speed
                                            diff_residual_time = road_length / platoon_speed - prev_platoon_residual_time
                                            if not first_controlled_platoon:
                                                first_controlled_platoon.append(cur_time)
                                            if diff_residual_time < delta:
                                                platoon_speed_dict[index_platoon] = road_length / (
                                                        prev_platoon_residual_time + delta)
                                                # number_platoon_controlled += 1
                                            else:
                                                # If residual time difference larger than delta, assign default platoon speed
                                                platoon_speed_dict[index_platoon] = platoon_speed
                                        # print("The assigned speed for this platoon is: "+str(platoon_speed_dict[index_platoon]))
                                        # If the previous platoon has exited, which means it is too far
                                        except traci.exceptions.TraCIException:
                                            platoon_speed_dict[index_platoon] = platoon_speed
                                        # print("The assigned speed for this platoon is: "+str(platoon_speed_dict[index_platoon]))
                                # Assign/maintain speed to all platoon in the controlled system:

                                for i in range(len(obtained_pla_list)):  # iteration of every platoon
                                    platoon(obtained_pla_list[i], platoon_speed_dict[index_platoon],
                                            desired_gap, l_co, h_co, slowDown_flag)  # control vehicle in selected platoon

                            if vehicle_bottleneck_count >= 25:
                                for veh_id in traci.vehicle.getIDList():
                                    if traci.vehicle.getTypeID(veh_id) == "Background" and \
                                            traci.vehicle.getPosition(veh_id)[0] > -1730 and \
                                            traci.vehicle.getPosition(veh_id)[0] < -1530:
                                        traci.vehicle.setMaxSpeed(veh_id, 0.6 * platoon_speed)
                                    else:
                                        traci.vehicle.setMaxSpeed(veh_id, platoon_speed)

                            counter += 1

                        # close the traci in SUMO
                        # print("number of controlled platoon is " +str(number_platoon_controlled))
                        # print("The first platoon controlled shows up at" + str(first_controlled_platoon[0]))
                        traci.close()

                        # # get final counter and average travel time
                        counter, ave_travel_time, background_count_all, platoon_count_all = xt.get_ave_time(
                            platoon_length, base_path)
                        # print("demand: " + str(demand))
                        # print("length: " + str(i_pla))
                        # print("background num: " + str(background_count_all))
                        # print("background flow: " + str(background_count_all / 3000.0))
                        # print("platoon num: " + str(platoon_count_all))
                        # print("platoon flow: " + str(platoon_count_all / 3000.0))
                        print("time: " + str(ave_travel_time))
                        return ave_travel_time


if __name__ == "__main__":
    # find SUMO path and start the sumo program
    try:
        sys.path.append(os.path.join(os.path.dirname(
            __file__), '..', '..', '..', '..', "tools"))
        sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
            os.path.dirname(__file__), "..", "..", "..")), "tools"))
        from sumolib import checkBinary
    except ImportError:
        sys.exit(
            "please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

    # open the interface between SUMO and Python
    import traci

    # choose whether to use GUI or not
    netconvertBinary = checkBinary('netconvert')
    sumoBinary = checkBinary(GUI_state)


    def get_options():
        opt_parser = optparse.OptionParser()
        opt_parser.add_option("--nogui", action="store_true",
                              default=False, help="simulate the commandline version of sumo")
        options, args = opt_parser.parse_args()
        return options


    options = get_options()

    # check binary
    '''
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    '''
    sumoBinary = checkBinary('sumo')
    avgTime = np.zeros((10, 10))  # 0.1-1.0 * 0.1-1.0 avgTime[行，轻][列，重]
    cur_h_co = 3  # current heavy coefficient
    cur_l_co = 5  # current light coefficient
    update_h_co = 0  # 四个方向的系数
    update_l_co = 0
    cur_min_avg_time = 100
    directions = {(0, 1), (1, 0), (-1, 0), (0, -1)}
    updated = False

    runner(0.5,0.1) # run for one time
    '''
    # run for several times
    # gradient decent
    while(1):
        print("##########----------Update----------###########")
        print("Current light coefficient:" + str(cur_l_co))
        print("Current heavy coefficient:" + str(cur_h_co))
        print("Current average time:\n" + str(avgTime))
        updated = False
        for direction in directions:
            pla_time = []
            update_l_co = cur_l_co + direction[0]
            update_h_co = cur_h_co + direction[1]
            if update_l_co <= 0 or update_l_co > 10 or \
                update_h_co <= 0 or update_h_co > 10 or \
                update_l_co < update_h_co or \
                avgTime[update_l_co-1][update_h_co-1] != 0:#如果之前已经计算过就不需要再计算了
                continue
            for loop_index in range(1): #循环主程序
                print("light coefficient" + str(update_l_co))
                print("heavy coefficient" + str(update_h_co))
                pla_time.append(runner(0.1*update_l_co,0.1*update_h_co))
            avgTime[update_l_co-1][update_h_co-1] = np.average(pla_time)
            print("update_l_co"+str(update_l_co))
            print("update_h_co"+str(update_h_co))
        for direction in directions: #找到四个方向里面梯度下降最快的
            update_l_co = cur_l_co + direction[0]
            update_h_co = cur_h_co + direction[1]
            if avgTime[update_l_co-1][update_h_co-1] != 0 and \
                    avgTime[update_l_co-1][update_h_co-1] < cur_min_avg_time:
                cur_min_avg_time = avgTime[update_l_co-1][update_h_co-1]
                cur_h_co = update_h_co
                cur_l_co = update_l_co
                updated = True
        if updated == False: #达到局部最优
            break
    print("Final light coefficient:" + str(cur_l_co))
    print("Final heavy coefficient:" + str(cur_h_co))
    print("Final average time:" + str(avgTime))
    '''
