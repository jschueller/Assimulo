import nose
import numpy as N
from assimulo.implicit_ode import *
from assimulo.problem import Implicit_Problem


class Test_Implicit_ODE:
    
    def test_init(self):
        """
        This tests the functionality of the method __init__.
        """
        def f(self, t, y, yd):
            pass
        res = Implicit_Problem()
        res.f = f
        
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 1, 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 1, 1, 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 'test', 'test', 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, [1.0 , 1.0], [1.0, 'test'])
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, None, [1.0 , 1.0, 1.0], [1.0, 1, 1])
        
        
        simulator = Implicit_ODE(res, [1 , 1.0], [2, 2.0], 1)
        assert simulator.t_cur == 1.0
        assert simulator.y_cur[0] == 1.0
        assert simulator.yd_cur[0] == 2.0
        
        
    def test_call(self):
        """
        This tests the functionality of the method __call__.
        """
        y0 = [0.0]
        yd0 = [1.0]
        my_Prob = Implicit_Problem()
        my_Prob.f = lambda t,x,xd: x

        simulator = IDA(my_Prob,y0,yd0)
        nose.tools.assert_raises(Implicit_ODE_Exception, simulator, -1.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, simulator, 'test')
        simulator(1.0,10)
        
        assert len(simulator.t) == 11 #11 Due to t0 is counted as well
        
    def test_reset(self):
        """
        This tests the functionality of the method reset.
        """
        y0 = [0.0]
        yd0 = [1.0]
        my_Prob = Implicit_Problem()
        my_Prob.f = lambda t,x,xd: x

        simulator = Implicit_ODE(my_Prob,y0,yd0)
        
        simulator.atol = 0.1
        simulator.rtol = 0.01
        simulator.maxsteps = 1000
        simulator.post_process = True
        simulator.verbosity = 2
        
        simulator.reset()
        
        assert simulator.atol == 0.1
        assert simulator.rtol == 0.01
        assert simulator.maxsteps == 1000
        assert simulator.post_process == True
        assert simulator.verbosity == 2
        
    
    
class Test_IDA:
    
    def setUp(self):
        """
        This function sets up the test case.
        """
        my_test_prob = Implicit_Problem()
        my_test_prob.f = lambda t,y,yd: y
        y0 = [1.0]
        yd0 = [1.0]

        self.simulator = IDA(my_test_prob, y0, yd0)
        
        
    def test_init(self):
        """
        This tests the functionality of the method __init__.
        """
        
        #assert self.simulator.res_fcn == 'Test function'
        assert self.simulator.suppress_alg == False
        assert self.simulator.algvar == [1.0]
        assert self.simulator.switches == None
        assert self.simulator.maxsteps == 10000
        assert self.simulator.verbosity == self.simulator.NORMAL
        assert self.simulator.y_cur[0] == 1.0
        
        nose.tools.assert_raises(Implicit_ODE_Exception, IDA, 'Test function', 'test', [1.0])
        nose.tools.assert_raises(Implicit_ODE_Exception, IDA, 'Test function', [1.0], [1.0], switches0='Error')
        
        my_Prob = Implicit_Problem()
        my_Prob.f = lambda t,x,xd,sw: x
        my_Prob.state_events = lambda t,x,xd,sw: x
        
        def jac(c,t,y,yd,sw):
            re = N.zeros([len(y),len(y)])
            return re
        
        my_Prob.jac = jac
        y0 = [1.0, 1.0, 1]
        yd0 = [1, 1, 1]
        
        switches = [True, False]

        simulator = IDA(my_Prob,y0,yd0, switches0=switches)
        
        #assert simulator.res_fcn == 'Test function'
        assert simulator.switches == switches
        assert simulator.yd_cur[0] == 1.0
        assert simulator.problem_data['RHS'] == simulator.res_fcn
        assert simulator.problem_data['JAC'] == simulator.jac
        assert simulator.problem_data['ROOT'] == simulator.state_events
    
    def test_interpolate(self):
        """
        This tests the functionality of the method interpolate.
        """
        f = lambda t,y,yd: y**0.25-yd
        
        prob = Implicit_Problem()
        prob.f = f
        
        sim = IDA(prob, [1.0],[1.0])
        sim.simulate(10., 100)
        y100 = sim.y
        t100 = sim.t
        sim.reset()
        sim.simulate(10.)
        
        nose.tools.assert_almost_equal(y100[-2], sim.interpolate(9.9,0),5)
    
    def test_handle_result(self):
        """
        This function tests the handle result.
        """
        f = lambda t,x,xd: x**0.25-xd
        def handle_result(solver, t ,y, yd):
            solver.temp+=1
        
        prob = Implicit_Problem()
        prob.f = f
        prob.handle_result = handle_result
        
        sim = IDA(prob, [1.0],[1.0])
        sim.temp = 0
        sim.store_cont = True
        assert sim.stats[0] == 0
        sim.simulate(10., 100)
        print sim.temp
        assert sim.stats[0] != 0
        assert sim.temp == 101
        sim.simulate(20, 40)
        print sim.temp
        assert sim.temp == 142
        
    def test_max_order(self):
        """
        This tests the functionality of the property maxord.
        """
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, "Test")
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, 1.0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, -1.0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, [1,1])
        
        
        self.simulator.maxord = -1
        assert self.simulator.maxord == 1
        self.simulator.maxord = 2
        assert self.simulator.maxord == 2
        self.simulator.maxord = 6
        assert self.simulator.maxord == 5
    
        
    def test_tout1(self):
        """
        This tests the functionality of the property tout1.
        """
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, 'Test')
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, [1,1])
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, 'Test')
        
        assert self.simulator.tout1 == 0.001
        self.simulator.tout1 = -0.001
        assert self.simulator.tout1 == -0.001
        self.simulator.tout1 = 1
        assert self.simulator.tout1 == 1.0
        
    def test_lsoff(self):
        """
        This tests the functionality of the property lsoff.
        """
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 'Test')
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 1.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 0.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, [1,1])
        
        assert self.simulator.lsoff == False
        self.simulator.lsoff = True
        assert self.simulator.lsoff == True
        self.simulator.lsoff = False
        assert self.simulator.lsoff == False
    
    def test_initstep(self):
        """
        This tests the funtionality of the property initstep.
        """
        
        def f(t,y,yd):
            res_0 = yd[0] - y[1]
            res_1 = yd[1] +9.82-0.01*y[1]**2
            return N.array([res_0,res_1])
            
        mod = Implicit_Problem()
        mod.f=f
        sim = IDA(mod, y0=[5.0,0.0], yd0=[0.0,9.82])
        
        sim.simulate(2.0)

        nose.tools.assert_almost_equal(sim.y[-1][0], -13.4746473811, places=7)
        
        sim = IDA(mod, y0=[5.0,0.0], yd0=[0.0,9.82])
        sim.initstep = 1e-10
        
        sim.simulate(2.0)

        nose.tools.assert_almost_equal(sim.y[-1][0], -13.4746596311, places=7)
        
    def test_time_event(self):
        """
        This tests the functionality of the time event function.
        """
        f = lambda t,x,xd,sw: xd-x
        
        def time_events(t, y, yd, sw):
            if sw[0]:
                return 1.0
            if sw[1]:
                return 3.0
            return None
        
        def handle_event(solver, event_info):
            
            if event_info[1]:
                solver.y_cur  = N.array([1.0])
                solver.yd_cur = N.array([1.0])
                
                if not solver.switches[0]:
                    solver.switches[1] = False
                
                if solver.switches[0]:
                    solver.switches[0] = False
        
        mod = Implicit_Problem()
        mod.f = f
        mod.time_events = time_events
        mod.handle_event = handle_event
        mod.switches0 = [True, True]
        
        sim = IDA(mod, [1.0],[1.0])
        
        sim.simulate(5.0)

        nose.tools.assert_almost_equal(sim.y[38], 1.0000000, 5)
        nose.tools.assert_almost_equal(sim.y[87], 1.0000000, 5)
        
        sim = IDA(mod, [1.0],[1.0])
        sim.simulate(2.0)
        
        nose.tools.assert_almost_equal(sim.t[-1], 2.0000000, 5)
        
        
    def test_usejac(self):
        """
        This tests the functionality of the property usejac.
        """
        f = lambda t,x,xd: N.array([xd[0]-x[1], xd[1]-9.82])       #Defines the rhs
        jac = lambda c,t,x,xd: N.array([[c,-1.],[0.,c]]) #Defines the jacobian

        imp_mod = Implicit_Problem()
        imp_mod.f = f
        imp_mod.jac = jac
        
        imp_sim = IDA(imp_mod, [1.0,0.0],[0.,-9.82])
        
        imp_sim.simulate(3,100)
        #imp_sim.plot()
        print imp_sim.y[-1]
        assert imp_sim.stats[3] == 0
        nose.tools.assert_almost_equal(imp_sim.y[-1][0], 45.1900000, 4)
        imp_sim.reset()
        imp_sim.usejac=False
        imp_sim.simulate(3.,100)

        nose.tools.assert_almost_equal(imp_sim.y[-1][0], 45.1900000, 4)
        assert imp_sim.stats[3] > 0
    
    def test_run(self):
        """
        This tests the functionality of the property run. (With jacobian)
        """
        pass
        
        
    def test_algvar(self):
        """
        This tests the functionality of the property algvar.
        """
        self.simulator.Integrator.dim = 3
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, 1)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, 1.0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [1,'hej',1])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, {'Test':'case'})
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [-1,0,1])
        

        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [1.0,1.0])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [3.0, 1.0, 1.0])
        
        vector = [1.0,0.0,1.0]
        vectorb = [True,False,True]
        vectori = [1,0,1]
        
        self.simulator.algvar = vectorb
        self.simulator.algvar = vectori
        self.simulator.algvar = vector
        nose.tools.assert_equal(self.simulator.algvar[0], vector[0])
        nose.tools.assert_equal(self.simulator.algvar[1], vector[1])
        nose.tools.assert_equal(self.simulator.algvar[2], vector[2])
        
        
    def test_suppress_alg(self):
        """
        This tests the functionality of the property suppress_alg.
        """
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, "Test")
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, [1,2])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, {'Test':'case'})
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 3)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 0.1)
        
        self.simulator.suppress_alg = True
        assert self.simulator.suppress_alg == True
        self.simulator.suppress_alg = False
        assert self.simulator.suppress_alg == False
        
    def test_make_consistency(self):
        """
        This tests the functionality of the method make_consistency.
        """
        def f(t,y,yd):
            res_1 = y[0] + y[1]+1.0
            res_2 = y[1]
            print res_1
            return N.array([res_1, res_2])
        my_Prob = Implicit_Problem()
        my_Prob.f = f
        
        y0 = [2.0, 2.0]
        yd0 = [1.0 , 0.0]
        simulator = IDA(my_Prob, y0, yd0)
        print simulator.Integrator.jacobian
        [y, yd] = simulator.make_consistent('IDA_Y_INIT')
        
        nose.tools.assert_almost_equal(y[1], 0.00000)
        nose.tools.assert_almost_equal(y[0], -1.0000)
        nose.tools.assert_almost_equal(yd[0], 1.0000)
        nose.tools.assert_almost_equal(yd[1], 0.0000)
     
    def test_is_disc(self):
        """
        This tests the functionality of the property is_disc.
        """
        class Prob_IDA(Implicit_Problem):
            f = lambda self,t,y,yd,sw: N.array([y[0]-1.0])
            state_events = lambda self,t,y,yd,sw: N.array([t-1.0, t])
            y0 = [1.0]
            yd0 = [1.0]
        switches = [False,True]
        res = Prob_IDA()
        simulator = IDA(res, switches0=switches)
        simulator(2.)
        
        #assert simulator.t[-1] == 1.0 #For now, this error serves as prof of discontinuities
        #assert simulator.is_disc == True
    
    def test_switches(self):
        """
        This tests that the switches are actually turned when override.
        """
        f = lambda t,x,xd,sw: N.array([xd[0]- 1.0])
        state_events = lambda t,x,xd,sw: N.array([x[0]-1.])
        def handle_event(solver, event_info):
            solver.switches = [False] #Override the switches to point to another instance
        
        mod = Implicit_Problem()
        mod.f = f
        mod.state_events = state_events
        mod.handle_event = handle_event
        
        sim = IDA(mod, [0.0], [1.0], switches0=[True])
        assert sim.switches[0] == True
        sim.simulate(3)
        assert sim.switches[0] == False
    
    def test_completed_step(self):
        """
        This tests the functionality of the method completed_step.
        """
        def f(t,y,yd):
            res_1 = y[0] + y[1]+1.0
            res_2 = y[1]
            return N.array([res_1, res_2])
        def completed_step(solver):
            solver._nstepevents += 1
        mod = Implicit_Problem()
        mod.f = f
        mod.completed_step = completed_step
        
        y0 = [-1.0, 0.0]
        yd0 = [1.0 , 0.0]
        sim = IDA(mod, y0, yd0)
        sim._nstepevents = 0
        
        sim.simulate(2., 100)
        assert len(sim.t) == 101
        assert sim._nstepevents == 22
        
        sim = IDA(mod, y0, yd0)
        sim._nstepevents = 0
        sim.simulate(2.)
        assert len(sim.t) == 23
        assert sim._nstepevents == 22
        
#class Test_IDAS:
#    """
#    Test sensitivity methods.
#    """
#    
#    def setUp(self):
#        """
#        This function sets up the test case.
#        """
#        mod = Implicit_Problem()
#        mod.f = lambda t,y,yd,p: N.array([0.0])
#        y0 = [1.0]
#        yd0 = [1.0]
#        p0 = [1.0]
#    
#        self.sim = IDA(mod, y0, yd0,p0=p0)
