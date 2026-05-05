#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 11:44:20 2020

@author: tessabourgonjon
Adapted by: Samuel Bakker
"""

from Distributions import Normal_distribution, Exponential_distribution

import numpy as np
from queue import Queue
from collections import defaultdict

# MAX_PERIOD = 200
# self.max_C = 20000
# MAX_RUN = 10
# MAX_S = 10
# MAX_AS = 5
# MAX_NR_STAIONS = 10
# MAX_NR_JOB_TYPES = 10


class RadiologyDept:
    """Simulates the radiology department.

    Attributes:
        list_scan (dict(Queue)): List of scans at a particular workstation waiting to be serviced.
        t_d (dict(dict)): Time of next departure for each server in each workstation. (inf if idle)
        t_a (dict): Time of next arrival for each source. (Two sources are available)
        t (float): Simulation time.
        n (int): Number of scans in the system.
        n_d (int): Number of scans that left the system.
        n_a (int): Number of scans that arrived in the system.
        routes (dict(dict)): Route to follow for each job type.
    """

    def initialize_functions(self, K):
        # Put all variables to zero
        # INPUT DATA RELATED TO SYSTEM JOBS #
        for i1 in range(0, self.max_C):
            self.current_station[i1] = 0

        # VARIABLES RELATED TO system SCANS #
        for i1 in range(0, self.nr_stations):
            self.n_ws[i1] = 0

        for i2 in range(0, K):
            self.mean_customers_system[i2] = 0
            self.tot_n[i2] = 0
            for i1 in range(0, self.nr_stations):
                self.tot_n_ws[i2][i1] = 0

        # PARAMETERS RELATED TO ARRIVAL OF SCANS #
        max_AS = 5
        for i1 in range(0, self.nr_stations):
            self.n_a_ws[i1] = 0

        for i2 in range(0, K):
            self.mean_interarrival_time[i2] = 0
            for i6 in range(0, max_AS):
                self.tot_lambda[i2][i6] = 0

            for i3 in range(0, self.max_C):
                self.time_arrival[i2][i3] = 0
                for i1 in range(0, self.nr_stations):
                    self.time_arrival_ws[i2][i1][i3] = 0
                self.scan_type[i3] = 0

        for i6 in range(0, max_AS):
            self.t_a[i6] = 0

        # PARAMETERS RELATED TO Processing OF SCANS #
        for i1 in range(0, self.nr_stations):
            self.n_d_ws[i1] = 0
            for i6 in range(0, self.nr_servers[i1]):
                self.t_d[i1][i6] = 0
                self.current_cust[i1][i6] = -1
            # for i6 in range(0, self.max_C):
            #     self.list_scan[i1][i6] = -1

        for i2 in range(0, K):
            self.mean_service_time[i2] = 0
            self.tot_mu[i2] = 0
            for i1 in range(0, self.nr_stations):
                for i3 in range(0, self.max_C):
                    self.time_service[i2][i1][i3] = 0

        # PARAMETERS RELATED TO waiting OF SCANS #
        for i2 in range(0, K):
            self.mean_waiting_time[i2] = 0
            self.waiting_time[i2] = 0
            self.mean_customers_queue[i2] = 0
            self.tot_n_queue[i2] = 0
            for i1 in range(0, self.nr_stations):
                self.tot_n_queue_ws[i2][i1] = 0
                for i3 in range(0, self.max_C):
                    self.waiting_time_job_ws[i2][i1][i3] = 0

        # VARIABLES RELATED TO Processed SCANS #
        for i2 in range(0, K):
            self.mean_system_time[i2] = 0
            for i3 in range(0, self.max_C):
                self.time_departure[i2][i3] = 0
                self.time_system[i2][i3] = 0
                for i1 in range(0, self.nr_stations):
                    self.time_departure_ws[i2][i1][i3] = 0
                    self.time_system_job_ws[i2][i1][i3] = 0

        for i3 in range(0, self.max_C):
            self.order_out[i3] = 0

        # OTHER PARAMETERS #
        for i2 in range(0, K):
            for i3 in range(0, self.nr_stations):
                for i1 in range(0, self.nr_servers[i3]):
                    self.idle[i2][i3][i1] = 0
        for i3 in range(0, self.nr_stations):
            self.rho_ws[i3] = 0
            for i1 in range(0, self.nr_servers[i3]):
                self.rho_ws_s[i3][i1] = 0

    def reset_simulation(self, K):  # Initialisation function
        self.max_C = 20000
        self.r += 1
        # SET INPUT VALUES #
        np.random.seed(0)  # ((i3+1)*K-run)
        # Ensure you each time use a different seed to get IID replications
        # INPUT RADIOLOGY DPT #

        self.nr_stations = 5  # Number of workstations
        self.nr_servers = {}  # Input number of servers per workstation
        self.nr_servers[0] = 3
        self.nr_servers[1] = 2
        self.nr_servers[2] = 4
        self.nr_servers[3] = 3
        self.nr_servers[4] = 4

        # INPUT JOB TYPES #

        self.nr_job_types = 4  # Number of scans, job types
        self.nr_workstations_job = {}  # Number of workstations per job type
        self.nr_workstations_job[0] = 4
        self.nr_workstations_job[1] = 3
        self.nr_workstations_job[2] = 5
        self.nr_workstations_job[3] = 3

        self.route = defaultdict(dict)  # Route to follow for each job type
        self.route[0][0] = 2  # JOB = 1
        self.route[0][1] = 0
        self.route[0][2] = 1
        self.route[0][3] = 4

        self.route[1][0] = 3  # JOB = 2
        self.route[1][1] = 0
        self.route[1][2] = 2

        self.route[2][0] = 1  # JOB = 3
        self.route[2][1] = 4
        self.route[2][2] = 0
        self.route[2][3] = 3
        self.route[2][4] = 2

        self.route[3][0] = 1  # JOB = 4
        self.route[3][1] = 3
        self.route[3][2] = 4

        self.current_station = {}  # Matrix that denotes the current station of a scan (sequence number)

        # INPUT ARRIVAL PROCESS #

        self.nr_arrival_sources = 2  # Number of arrival sources
        # Number of scans arrived to the system
        self.n_a = 0
        self.t_lambda = 0
        self.n_a_ws = {}  # Number of scans arrived to a particular workstation
        self.t_a = {}  # Time of next arrival for each source
        self.first_ta = 0
        # Source of next arrival
        self.index_arr = 0
        self.tot_lambda = defaultdict(dict)
        self.scan_type = {}  # Type of scan arriving
        self.time_arrival = defaultdict(dict)  # Time of arrival of the scan to the ancillary services
        self.time_arrival_ws = defaultdict(lambda: defaultdict(dict))  # Time of arrival of a particular scan to a particular workstation
        self.mean_interarrival_time = {}

        # Arrival from radiology department
        self.lamb = {}  # Arrival rate
        self.lamb[0] = 1 / 0.25  # Input arrival rate = 1/mean interarrival time
        self.cum_distr_scans = defaultdict(dict)  # Cumulative(!) distribution of job types per source
        self.cum_distr_scans[0][0] = 0.2  # SOURCE = 1
        self.cum_distr_scans[0][1] = 0.4
        self.cum_distr_scans[0][2] = 0.5
        self.cum_distr_scans[0][3] = 1

        # Arrival from other services
        self.lamb[1] = 1 / 1  # Input arrival rate = 1/mean interarrival time
        self.cum_distr_scans[1][0] = 0  # SOURCE = 2
        self.cum_distr_scans[1][1] = 0.4
        self.cum_distr_scans[1][2] = 0.4
        self.cum_distr_scans[1][3] = 1

        # INPUT SERVICE PROCESS #
        self.perc_again = 0.02  # The probability that a scan should be re-evaluated at a particular workstation
        self.n_d_ws = {}  # Number of scans handled in a particular workstation
        self.t_d = defaultdict(dict)  # Time of next departure for each server in each workstation
        # First departure time over all sources
        # # Station with first departure
        # Server with first departure
        self.mean_service_time = {}  # Calculated average service time
        # Generated service time
        self.n_d = self.first_td = self.index_dep_station = self.index_dep_server = self.t_mu = 0
        self.tot_mu = {}  # Total service time generated
        self.time_service = defaultdict(lambda: defaultdict(dict))  # Service time per customer and workstation
        self.current_cust = defaultdict(dict)  # Customer handles by a particular workstation and server
        # self.list_scan = defaultdict(dict)  # list of customers processed at a particular workstation on a particular point in time
        self.list_scan = defaultdict(Queue)

        self.mu = defaultdict(dict)  # Processing time per ws and job type
        self.mu[0][0] = 12  # WS1, J1
        self.mu[0][1] = 15
        self.mu[0][2] = 15
        self.mu[0][3] = 0
        
        self.mu[1][0] = 20  # WS2, J1
        self.mu[1][1] = 0  
        self.mu[1][2] = 21
        self.mu[1][3] = 18
        
        self.mu[2][0] = 16  # WS3, J1
        self.mu[2][1] = 14  
        self.mu[2][2] = 10
        self.mu[2][3] = 0

        self.mu[3][0] = 0  # WS4, J1
        self.mu[3][1] = 20
        self.mu[3][2] = 24
        self.mu[3][3] = 13

        self.mu[4][0] = 17  # WS5, J1
        self.mu[4][1] = 0
        self.mu[4][2] = 15
        self.mu[4][3] = 16

        self.var = defaultdict(dict)  # Processing variance per ws and job type
        self.var[0][0] = 2  # WS1, J1
        self.var[0][1] = 2
        self.var[0][2] = 3
        self.var[0][3] = 0

        self.var[1][0] = 4  # WS2, J1
        self.var[1][1] = 0
        self.var[1][2] = 3
        self.var[1][3] = 3

        self.var[2][0] = 4  # WS3, J1
        self.var[2][1] = 2
        self.var[2][2] = 1
        self.var[2][3] = 0

        self.var[3][0] = 0  # WS4, J1
        self.var[3][1] = 3
        self.var[3][2] = 4
        self.var[3][3] = 2

        self.var[4][0] = 4  # WS5, J1
        self.var[4][1] = 0
        self.var[4][2] = 3
        self.var[4][3] = 4

        self.sigma = defaultdict(dict)  # Processing stdev per ws and job type
        self.sigma[0][0] = np.sqrt(self.var[0][0])  # WS1, J1
        self.sigma[0][1] = np.sqrt(self.var[0][1])
        self.sigma[0][2] = np.sqrt(self.var[0][2])
        self.sigma[0][3] = np.sqrt(self.var[0][3])

        self.sigma[1][0] = np.sqrt(self.var[1][0])  # WS2, J1
        self.sigma[1][1] = np.sqrt(self.var[1][1])
        self.sigma[1][2] = np.sqrt(self.var[1][2])
        self.sigma[1][3] = np.sqrt(self.var[1][3])

        self.sigma[2][0] = np.sqrt(self.var[2][0])  # WS3, J1
        self.sigma[2][1] = np.sqrt(self.var[2][1])
        self.sigma[2][2] = np.sqrt(self.var[2][2])
        self.sigma[2][3] = np.sqrt(self.var[2][3])

        self.sigma[3][0] = np.sqrt(self.var[3][0])  # WS4, J1
        self.sigma[3][1] = np.sqrt(self.var[3][1])
        self.sigma[3][2] = np.sqrt(self.var[3][2])
        self.sigma[3][3] = np.sqrt(self.var[3][3])

        self.sigma[4][0] = np.sqrt(self.var[4][0])  # WS5, J1
        self.sigma[4][1] = np.sqrt(self.var[4][1])
        self.sigma[4][2] = np.sqrt(self.var[4][2])
        self.sigma[4][3] = np.sqrt(self.var[4][3])

        # GENERAL DISCRETE EVENT SIMULATION PARAMETERS #

        self.N = 10000  # Number of scans (Stop criterion)
        # Simulation time
        self.t = 0

        # VARIABLES RELATED TO system SCANS #
        # Number of scans in the system
        self.n = 0
        self.n_ws = {}  # Number of scans at a particular workstation
        self.mean_customers_system = {}
        self.tot_n = {}  # Number of customers in the system over time
        self.tot_n_ws = defaultdict(dict)  # Number of customers in a workstation over time

        # VARIABLES RELATED TO waiting OF SCANS #
        self.mean_waiting_time = {}
        self.waiting_time = {}
        self.waiting_time_job_ws = defaultdict(lambda: defaultdict(dict))  # Waiting time for a job on a particular workstation

        self.mean_customers_queue = {}
        self.tot_n_queue = {}
        self.tot_n_queue_ws = defaultdict(dict)  # Total number of scans in queue at workstation over time

        # VARIABLES RELATED TO Processed SCANS #
        self.time_departure = defaultdict(dict)
        self.time_departure_ws = defaultdict(lambda: defaultdict(dict))

        self.time_system = defaultdict(dict)
        self.time_system_job_ws = defaultdict(lambda: defaultdict(dict))

        self.order_out = {}
        self.mean_system_time = {}

        # OTHER PARAMETERS #
        self.infinity = 999999999
        self.rho = 0
        self.idle = defaultdict(lambda: defaultdict(dict))
        self.rho_ws_s = defaultdict(dict)
        self.rho_ws = {}

        # VARIABLES RELATED TO CLOCK TIME #

        # PUT ALL VARIABLES TO ZERO #
        self.initialize_functions(K)

        # INITIALISE SYSTEM #

        # DETERMINE FIRST ARRIVAL AND FIRST DEPARTURE #
        for stat_idx in range(0, self.nr_stations):
            for serv_idx in range(0, self.nr_servers[stat_idx]):
                self.t_d[stat_idx][serv_idx] = self.infinity

        for source_idx in range(self.nr_arrival_sources):
            self.t_a[source_idx] = Exponential_distribution(self.lamb[source_idx])

        self.index_arr = 0
        self.first_ta = self.infinity

        for source_idx in range(self.nr_arrival_sources):
            if self.first_ta > self.t_a[source_idx]:
                self.first_ta = self.t_a[source_idx]
                self.index_arr = source_idx

        self.tot_lambda[self.r][self.index_arr] = self.first_ta

    def __init__(self, K):
        self.r = -1
        self.utilization_per_departure = []

        
    def arrival_event(self):
        """Arrival in the system.

        This method simulates the arrival of a new scan in the system. It determines the scan-type, the workstation to which the scan should go first, and the arrival time of the scan.
        """
        # ? update statistics for period [t, t_a]
        self.tot_n[self.r] += (self.t_a[self.index_arr] - self.t) * self.n
        for station_idx in range(0, self.nr_stations):
            self.tot_n_ws[self.r][station_idx] += (self.t_a[self.index_arr] - self.t) * self.n_ws[station_idx]

        for station_idx in range(0, self.nr_stations):
            if self.n_ws[station_idx] >= self.nr_servers[station_idx]:
                self.tot_n_queue_ws[self.r][station_idx] += (self.t_a[self.index_arr] - self.t) * (self.n_ws[station_idx] - self.nr_servers[station_idx])
                self.tot_n_queue[self.r] += (self.t_a[self.index_arr] - self.t) * (self.n_ws[station_idx] - self.nr_servers[station_idx])

        for station_idx in range(0, self.nr_stations):
            for server_idx in range(0, self.nr_servers[station_idx]):
                if self.t_d[station_idx][server_idx] == self.infinity:
                    self.idle[self.r][station_idx][server_idx] += (self.t_a[self.index_arr] - self.t)

        # - increment simulation time
        self.t = self.t_a[self.index_arr]

        # - generate job type
        j1 = np.random.uniform(0, 1)
        self.scan_type[self.n_a] = 0
        while j1 > self.cum_distr_scans[self.index_arr][self.scan_type[self.n_a]]:
            self.scan_type[self.n_a] += 1

        # - determine station for this job
        self.current_station[self.n_a] = 0

        sc_type = self.scan_type[self.n_a]
        curr_stat = self.current_station[self.n_a]
        next_stat = self.route[sc_type][curr_stat]
        # - set arrival time
        self.time_arrival_ws[self.r][next_stat][self.n_a] = self.t
        self.time_arrival[self.r][self.n_a] = self.t

        # - increment number of arrivals
        self.n_a_ws[next_stat] += 1
        self.n_ws[next_stat] += 1

        # ? check if machines are busy
        if self.n_ws[next_stat] <= self.nr_servers[next_stat]:
            # There is a server available
            for server_idx in range(0, self.nr_servers[next_stat]):
                # - check the departure time of each server
                if self.t_d[next_stat][server_idx] == self.infinity:
                    # ! server found
                    break

            self.t_mu = Normal_distribution(
                self.mu[next_stat][sc_type],
                self.sigma[next_stat][sc_type]
            ) / 60
            self.time_service[self.r][next_stat][self.n_a] = self.t_mu
            # - because job can start, delay is 0
            self.waiting_time_job_ws[self.r][next_stat][self.n_a] = 0
            # - make machine busy
            self.t_d[next_stat][server_idx] = self.t + self.t_mu
            self.tot_mu[self.r] += self.t_mu
            # - keep track of current customer being served by this server
            self.current_cust[next_stat][server_idx] = self.n_a
        else:
            self.list_scan[next_stat].put(self.n_a)
            # queue_pos = 0
            # for queue_pos in range(0, self.n_ws[next_stat]):
            #     if self.list_scan[next_stat][queue_pos] == -1:
            #         break
            # # - add to queue
            # self.list_scan[next_stat][queue_pos] = self.n_a
        print(f"Arrival event\tJob {self.n_a}\tSource {self.index_arr}\tTime {self.t}\tScan Type {sc_type}")
        self.n_a += 1
        self.n += 1
        # ? schedule next arrival
        self.t_lambda = Exponential_distribution(self.lamb[self.index_arr])
        self.t_a[self.index_arr] = self.t + self.t_lambda
        self.tot_lambda[self.r][self.index_arr] += self.t_lambda

    def departure_event(self):
        curr_cust = self.current_cust[self.index_dep_station][self.index_dep_server]
        sc_type = self.scan_type[curr_cust]

        # ? 1. Update statistics:
        # - update total number of customers per workstation
        self.tot_n[self.r] = (self.t_d[self.index_dep_station][self.index_dep_server] - self.t) * self.n
        for station_idx in range(0, self.nr_stations):
            self.tot_n_ws[self.r][station_idx] += (self.t_d[self.index_dep_station][self.index_dep_server] - self.t) * self.n_ws[station_idx]

        # - update total number of customers in queue per workstation
        for station_idx in range(0, self.nr_stations):
            if self.n_ws[station_idx] > self.nr_servers[station_idx]:
                self.tot_n_queue_ws[r][station_idx] += (self.t_d[self.index_dep_station][self.index_dep_server] - self.t) * self.n_ws[station_idx]
                self.tot_n_queue[r] += (self.t_d[self.index_dep_station][self.index_dep_server] - self.t) * (self.n_ws[station_idx] - self.nr_servers[station_idx])

        # - update total amount of idle time
        for station_idx in range(0, self.nr_stations):
            for server_idx in range(0, self.nr_servers[station_idx]):
                if self.t_d[station_idx][server_idx] == self.infinity:
                    self.idle[self.r][station_idx][server_idx] += (self.t_d[self.index_dep_station][self.index_dep_server] - self.t)

        # ? 2. update variables
        # - time
        self.t = self.t_d[self.index_dep_station][self.index_dep_server]
        # - store departure time of customer
        self.time_departure_ws[self.r][self.index_dep_station][curr_cust] = self.t
        # - store time in ws of customer
        self.time_system_job_ws[self.r][self.index_dep_station][curr_cust] += (self.t - self.time_arrival_ws[self.r][self.index_dep_station][self.current_cust[self.index_dep_station][self.index_dep_server]])
        # - increment number of departures and decrement the number of customers at this ws
        self.n_d_ws[self.index_dep_station] += 1
        self.n_ws[self.index_dep_station] -= 1
        # - send current customer to next station
        self.current_station[curr_cust] += 1
        curr_stat = self.current_station[curr_cust]

        # - remove scan from queue of current station
        # for task_queue_idx in range(0, self.n_ws[self.index_dep_station] + 1):
        #     if self.list_scan[self.index_dep_station][task_queue_idx] == curr_cust:
        #         self.list_scan[self.index_dep_station][task_queue_idx] = -1
        #         break
        # start_idx_queue = task_queue_idx
        # for task_queue_idx in range(start_idx_queue, self.n_ws[self.index_dep_station] + 1):
        #     self.list_scan[self.index_dep_station][task_queue_idx] = self.list_scan[self.index_dep_station][task_queue_idx + 1]
        # self.list_scan[self.index_dep_station][task_queue_idx] = -1

        print(f"Departure event\tJob {curr_cust}\tWorkstation {self.index_dep_station}\tServer {self.index_dep_server}\tTime {self.t}\tCurrent station {curr_stat} of {self.nr_workstations_job[sc_type]}\n")

        # ? 3. determine next departure (if any)

        if curr_stat < self.nr_workstations_job[sc_type]:
            next_station = self.route[sc_type][curr_stat]
            # ! this customer still has jobs to do:
            # - based on route: increment amount of jobs at the next station
            self.n_ws[next_station] += 1
            # - increment number of arrived customers at the next station
            self.n_a_ws[next_station] += 1
            # - arrivaltime at next workstation
            self.time_arrival_ws[self.r][next_station][curr_cust] = self.t

            if self.n_ws[next_station] <= self.nr_servers[next_station]:
                # ! server is available
                for server_idx in range(0, self.nr_servers[next_station]):
                    if self.t_d[next_station][server_idx] == self.infinity:
                        break

                # for i2 in range(0, self.nr_servers[next_station]):
                #     if self.list_scan[next_station][i2] == -1:
                #         self.list_scan[next_station][i2] = curr_cust
                #         break

                # - service time
                self.t_mu = Normal_distribution(
                    self.mu[next_station][sc_type],
                    self.sigma[next_station][sc_type]
                ) / 60
                self.time_service[self.r][next_station][curr_cust] = self.t_mu
                # - delay = 0 because a server was available
                self.waiting_time_job_ws[self.r][next_station][curr_cust] = 0
                # - server should be set to busy
                self.t_d[next_station][server_idx] = self.t + self.t_mu
                self.tot_mu[self.r] += self.t_mu
                # - shift customer to next station
                self.current_cust[next_station][server_idx] = curr_cust
            else:
                # ! no server available
                # - add to queue
                self.list_scan[next_station].put(curr_cust)
                # self.list_scan[next_station][self.n_ws[next_station] - 1] = curr_cust
        else:
            # ! this customer is done
            # - update statistics
            self.order_out[self.n_d] = curr_cust
            self.n_d += 1
            # - decrement number of customers in the system
            self.n -= 1
            self.time_departure[self.r][curr_cust] = self.t
            self.time_system[self.r][curr_cust] = self.t - self.time_arrival[self.r][curr_cust]
            print(f"JOB {curr_cust} FINISHED AT TIME: {self.t}")

        # ! determine next scan on this station
        if self.n_ws[self.index_dep_station] >= self.nr_servers[self.index_dep_station]:
            # there are still scans to do
            # self.current_cust[self.index_dep_station][self.index_dep_server] = self.list_scan[self.index_dep_station][0]
            curr_cust = self.list_scan[self.index_dep_station].get()
            self.current_cust[self.index_dep_station][self.index_dep_server] = curr_cust
            sc_type = self.scan_type[curr_cust]
            curr_stat = self.current_station[curr_cust]
            # - determine departure time for newly arrived scan
            self.t_mu = Normal_distribution(
                self.mu[self.route[sc_type][curr_stat]][sc_type],
                self.sigma[self.route[sc_type][curr_stat]][sc_type]
            ) / 60
            # - store service time
            self.time_service[self.r][self.route[sc_type][curr_stat]][curr_cust] = self.t_mu
            self.waiting_time_job_ws[self.r][self.route[sc_type][curr_stat]][curr_cust] = \
                self.t - self.time_arrival_ws[self.r][self.index_dep_station][curr_cust]
            # - make server busy (by setting departure time)
            self.t_d[self.index_dep_station][self.index_dep_server] = self.t + self.t_mu
            self.tot_mu[self.r] += self.t_mu
        else:
            # - make server in this station idle
            self.t_d[self.index_dep_station][self.index_dep_server] = self.infinity

        # Calculate total idle time so far (accumulated correctly)
        total_idle_so_far = 0
        for i in range(self.nr_stations):
            for j in range(self.nr_servers[i]):
                total_idle_so_far += self.idle[self.r][i][j]
        
        # Compute utilization at this moment
        total_servers = sum(self.nr_servers[i] for i in range(self.nr_stations))
        utilization_now = 1 - (total_idle_so_far / (self.t * total_servers))
    

        # Store it for output
        self.utilization_per_departure.append(utilization_now)


    def radiology_system(self):
        # loop until N scans are done
        while self.n_d < self.N:
            # ? get next arrival time:
            self.first_ta = self.infinity
            for i1 in range(0, self.nr_arrival_sources):
                if self.first_ta > self.t_a[i1]:
                    self.first_ta = self.t_a[i1]
                    self.index_arr = i1

            # ? get next departure time:
            self.first_td = self.infinity
            for st in range(0, self.nr_stations):
                for serv in range(0, self.nr_servers[st]):
                    # print(f"station {st} server {serv} time {self.t_d[st][serv]}")
                    if self.first_td > self.t_d[st][serv]:
                        self.first_td = self.t_d[st][serv]
                        self.index_dep_server = serv
                        self.index_dep_station = st
            if self.first_ta < self.first_td:
                # * arrival event
                self.arrival_event()
            else:
                # * departure event
                self.departure_event()
            # assertion checks:
            for station in range(0, self.nr_stations):
                num_busy = 0
                for server in range(0, self.nr_servers[station]):
                    if self.t_d[station][server] != self.infinity:
                        num_busy += 1
                qsize = self.list_scan[station].qsize()
                assert qsize + num_busy == self.n_ws[station]

    def output(self):
        file1 = open("Output_Radiology.txt", "w")
        for i1 in range(0, self.nr_stations):
            file1.write('Utilisation servers Station WS %d:\t' % i1)
            for i2 in range(0, self.nr_servers[i1]):
                j1 = self.idle[self.r][i1][i2] / self.t
                self.rho_ws_s[i1][i2] = 1 - j1
                file1.write('%lf\t' % self.rho_ws_s[i1][i2])
            file1.write('\n')
        file1.write('\n')
        for i1 in range(0, self.nr_stations):
            file1.write('Avg utilisation Station WS %d:\t' % i1)
            for i2 in range(0, self.nr_servers[i1]):
                self.rho_ws[i1] += self.rho_ws_s[i1][i2]
            self.rho_ws[i1] = self.rho_ws[i1] / self.nr_servers[i1]
            file1.write('%lf\n' % self.rho_ws[i1])
        file1.write('\n')

        for i1 in range(0, self.nr_stations):
            self.rho += self.rho_ws[i1]
        self.rho /= self.nr_stations
        file1.write('Overall avg utilisation: %lf\n' % self.rho)
        file1.write('\n')

        for i1 in range(1195, self.N):  # PRINT system time = cycle time (observations and running average)
            self.mean_system_time[self.r] += self.time_system[self.r][self.order_out[i1]]
        file1.write('Cycle time\n\n')
        j1 = self.mean_system_time[self.r] / self.N
        file1.write('Avg cycle time: %lf\n\n' % j1)

        self.mean_system_time[self.r] = 0
        file1.write('Number\tCycle Time\tRunning Avg Cycle Time\tUtilization\tRunning Avg Utilization\tObjective Function\tRunning Avg Objectif Function \n')

        utilization_list = []

        for i1 in range(1195, self.N):
            job_id = self.order_out[i1]
            self.mean_system_time[self.r] += self.time_system[self.r][job_id]
            running_avg_ct = self.mean_system_time[self.r] / (i1 + 1)

            current_util = self.utilization_per_departure[i1]
            utilization_list.append(current_util)
            moving_avg_util = sum(utilization_list) / len(utilization_list)

            obj_fn_values = self.time_system[self.r][job_id] - 10 * current_util

            running_avg_obj_func = running_avg_ct - 10 * moving_avg_util

            file1.write(f"{i1}\t{self.time_system[self.r][job_id]:.6f}\t{running_avg_ct:.6f}\t{current_util:.6f}\t{moving_avg_util:.6f}\t{obj_fn_values:.6f}\t{running_avg_obj_func:.6f}\n")

if __name__ == "__main__":
    L = 1
    for run in range(0, L):
        K = 1
        radiodept = RadiologyDept(K)
        # radiodept.run = run
        for r in range(0, K):
            radiodept.reset_simulation(K)
            radiodept.radiology_system()
            radiodept.output()
