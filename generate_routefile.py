#import numpy as np
import random


def generate_routefile(total_time, demand, pla_veh_num, pla_veh_frc, seed, gap, pla_state):
    # pla_veh_num = 10
    #print('Current demand: ', demand)
    #print('Current platoon length: ', pla_veh_num)
    #print('Current platoon fraction: ', pla_veh_frc)
    #print('Current seed: ', seed)
    #print('Desired Gap: ', gap)
    #print('Platoon State: ', pla_state)
    pla_time = []
    vehicle_length = 10
    with open("data/hello.rou.xml", "w") as routes:  # tau = 1.35, 1.65, 1.45
        print("""<?xml version="1.0" encoding="UTF-8"?>

<routes>
	<route id="route0" edges="lane_1 lane_2 lane_3" />
	<route id="route1" edges="lane_1 lane_4" />

	<!--vType id="Follower" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.1' lcSpeedGain='0.1' tau = "1.35" length="10.0" lcKeepRight='0.1'/-->
	<!--vType id="Background" vClass="passenger" departSpeed='26.82'  maxSpeed='26.82' lcPushy='0.1' lcKeepRight='20.0' tau = "1.65" minGap = "2.5" decel='6.0' emergencyDecel='6.0'/-->
	<!--vType id="Leader" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.7' lcSpeedGain='0.1' lcKeepRight='0.1' length="10.0" tau = "1.45" minGap = "2.5" lcStrategic="0.28"/-->

	<vType id="Follower" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.1' lcSpeedGain='0.1' tau="1.35" length="5.0" lcKeepRight='0.1'/>
	<vType id="Background" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.1' lcKeepRight='20.0' tau = "1.65" minGap = "2.5" decel='6.0' emergencyDecel='6.0'/>
	<vType id="Leader" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.7' lcSpeedGain='0.1' lcKeepRight='0.1' length="5.0" tau = "1.45" minGap = "2.5" lcStrategic="0.28"/>
	<vType id="Test" vClass="passenger" departSpeed='26.82' maxSpeed='26.82' lcPushy='0.7' lcSpeedGain='0.1' lcKeepRight='0.1' length="%i" tau = "1.45" minGap = "2.5" lcStrategic="0.28"/>
	""" % (pla_veh_num * vehicle_length + (pla_veh_num - 1) * (gap - vehicle_length)), file=routes)

        total_time = 7200
        total_vol = demand
        times = demand / (pla_veh_num * 3)  # 出现队列的时间段次数
        space_time = total_time / times
        background_vol = total_vol * (1 - pla_veh_frc)
        background_vol_each_space = background_vol / times
        background_space_time = total_time / background_vol
        iteration_time = round(total_time / background_space_time)
        platoon_vol = total_vol * pla_veh_frc / (pla_veh_num * 3 * pla_veh_frc)

        pla_tt_index = 0

        pla_depart_tt = 0
        p = pla_veh_frc
        pla_num_each_timeslot = pla_veh_num * 3 * p
        nonpla_num_each_timeslot = round(pla_veh_num * 3 * (1 - p))
        times = int(times)
        a = range(3 * times)
        p_1_pos = random.sample(a, round(3 * p * times))
        pro = [0 for i in range(3 * times)]
        for i in p_1_pos:
            pro[i] = 1
        p0 = pro[0: times]
        p1 = pro[times: 2 * times]
        p2 = pro[2 * times: 3 * times]
        count = 0
        flag = 0
        plas = 0
        i = 0
        while (i < iteration_time):
            # print("i: "+str(i))
            if (count <= nonpla_num_each_timeslot - 1):
                # print("count:" + str(count))
                print(
                    '    <vehicle id="Veh_%i" type="Background" color="1,0,0" route="route0" depart="%f" departLane="random" departSpeed="26.82"/>' % (
                    i, pla_depart_tt), file=routes)

                pla_depart_tt = pla_depart_tt + background_space_time
                count += 1
                i += 1
            else:
                # print("count:" + str(count))
                count = 0
                flag = 1

            while flag:
                # print("plas" + str(plas))
                pla_lane_num = 0
                if (p0[plas] == 1):
                    for j in range(pla_veh_num):
                        if j == 0:
                            print(
                                '    <vehicle id="%i_%i" type="Leader" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index, j, pla_depart_tt, 0), file=routes)
                        else:
                            print(
                                '    <vehicle id="%i_%i" type="Follower" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index, j, pla_depart_tt, 0), file=routes)
                    pla_lane_num += 1
                if (p1[plas] == 1):
                    for j in range(pla_veh_num):
                        if j == 0:
                            print(
                                '    <vehicle id="%i_%i" type="Leader" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index + pla_lane_num, j, pla_depart_tt, 1), file=routes)
                        else:
                            print(
                                '    <vehicle id="%i_%i" type="Follower" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index + pla_lane_num, j, pla_depart_tt, 1), file=routes)
                    pla_lane_num += 1
                if (p2[plas] == 1):
                    for j in range(pla_veh_num):
                        if j == 0:
                            print(
                                '    <vehicle id="%i_%i" type="Leader" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index + pla_lane_num, j, pla_depart_tt, 2), file=routes)
                        else:
                            print(
                                '    <vehicle id="%i_%i" type="Follower" color="1,1,0" route="route0" depart="%f" departLane="%i" departSpeed="26.82"/>'
                                % (pla_tt_index + pla_lane_num, j, pla_depart_tt, 2), file=routes)
                    pla_lane_num += 1
                for k in range(pla_tt_index, pla_tt_index + pla_lane_num):
                    pla_time.append(k)
                pla_tt_index += pla_lane_num
                flag = 0
                plas += 1
        print("</routes>", file=routes)
    return (pla_time)
