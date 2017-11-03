
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import os
import sys
import htmlTools
import olex
import olx
import gui


import time
debug = bool(OV.GetParam("olex2.debug", False))

get_template = gui.tools.TemplateProvider.get_template

instance_path = OV.DataDir()

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

l = open(os.sep.join([p_path, 'def.txt'])).readlines()
d = {}
for line in l:
  line = line.strip()
  if not line or line.startswith("#"):
    continue
  d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d['p_name']
p_htm = d['p_htm']
p_img = eval(d['p_img'])
p_scope = d['p_scope']

OV.SetVar('HARp_plugin_path', p_path)

from PluginTools import PluginTools as PT

from gui.images import GuiImages
GI=GuiImages()

class HARp(PT):

  def __init__(self):
    super(HARp, self).__init__()
    self.p_name = p_name
    self.p_path = p_path
    self.p_scope = p_scope
    self.p_htm = p_htm
    self.p_img = p_img
    self.deal_with_phil(operation='read')
    self.print_version_date()
    if not from_outside:
      self.setup_gui()
    # END Generated =======================================
    options = {
      "settings.tonto.HAR.basis.name": ("def2-SVP", "basis"),
      "settings.tonto.HAR.method": ("rhf", "scf"),
      "settings.tonto.HAR.hydrogens": ("positions+Uaniso",),
      "settings.tonto.HAR.extinction.refine": ("False", "extinction"),
      "settings.tonto.HAR.convergence.value": ("0.0001", "dtol"),
      "settings.tonto.HAR.cluster.radius": ("0", "cluster-radius"),
      "settings.tonto.HAR.intensity_threshold.value": ("3", "fos"),
      "settings.tonto.HAR.dispersion": ("false",),
      "settings.tonto.HAR.autorefine": ("true",),
    }
    self.options = options

    self.jobs_dir = os.path.join(olx.DataDir(), "jobs")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    self.jobs = []
    if sys.platform[:3] == 'win':
      self.exe = olx.file.Which("hart.exe")
    else:
      self.exe = olx.file.Which("hart")
    if os.path.exists(self.exe):
      self.basis_dir = os.path.join(os.path.split(self.exe)[0], "basis_sets").replace("\\", "/")
      if os.path.exists(self.basis_dir):
        basis_list = os.listdir(self.basis_dir)
        basis_list.sort()
        self.basis_list_str = ';'.join(basis_list)
      else:
        self.basis_list_str = None
    else:
      self.basis_list_str = None
      self.basis_dir = None

    self.set_defaults()

  def set_defaults(self):
    for k,v in self.options.iteritems():
      olx.SetVar(k, v[0])

  def launch(self):
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return
    j = Job(self, olx.FileName())
    j.launch()
    olx.html.Update()


  def getBasisListStr(self):
    return self.basis_list_str

  def list_jobs(self):
    d = {}
    self.jobs = []
    for j in os.listdir(self.jobs_dir):
      fp  = os.path.join(self.jobs_dir, j)
      jof = os.path.join(fp, "job.options")
      if os.path.isdir(fp) and os.path.exists(jof):
        self.jobs.append(Job(self, j))
    sorted(self.jobs, key=lambda s: s.date)
    rv = get_template('table_header', path=p_path)

    status_running = "<font color='%s'><b>Running</b></font>" %OV.GetParam('gui.orange')
    status_completed = "<font color='%s'><b>Finished</b></font>" %OV.GetParam('gui.green')
    status_error = "<font color='%s'><b>Error!</b></font>" %OV.GetParam('gui.red')
    status_stopped = "<font color='%s'><b>Stopped</b></font>" %OV.GetParam('gui.red')
    status_nostart = "<font color='%s'><b>No Start</b></font>" %OV.GetParam('gui.red')

    for i in range(len(self.jobs)):
      OUT_file = self.jobs[i].out_fn

      try:
        if not os.path.exists(OUT_file):
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_nostart)
        else:
          os.rename(OUT_file, "_.txt")
          os.rename("_.txt", OUT_file)
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_stopped)
      except:
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_running)

      error = "--"
      if os.path.exists(self.jobs[i].error_fn):
        _ = os.stat(self.jobs[i].error_fn).st_size == 0
        #TO DO: go through error file and look for the keyword ERROR, ignore Warnings and empty lines
        if _:
          error = "--"
        else:
          error = "<a target='Open .err file' href='exec -o getvar(defeditor) %s'>ERR</a>" %self.jobs[i].error_fn
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)

      dump = "--"
      if os.path.exists(self.jobs[i].dump_fn):
        dump = "<a target='Open .dump file' href='exec -o getvar(defeditor) %s'>DUMP</a>" %self.jobs[i].dump_fn
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)

      analysis = "--"
      if os.path.exists(self.jobs[i].analysis_fn):
        analysis = "<a target='Open analysis file' href='exec -o getvar(defeditor) %s>>spy.tonto.HAR.getAnalysisPlotData(%s)'>Open</a>" %(
          self.jobs[i].analysis_fn, self.jobs[i].analysis_fn)
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_completed)


      d['job_result_filename'] = self.jobs[i].result_fn
      d['job_result_name'] = self.jobs[i].name
      d['ct'] = time.strftime("%b %d %H:%M", time.localtime(self.jobs[i].date))
      d['status'] = status
      d['error'] = error
      d['dump'] = dump
      d['analysis'] = analysis
      del_file = os.path.dirname(d['job_result_filename'])
      d['delete'] = del_button = GI.get_action_button_html('delete', "spy.tonto.har.del_dir(%s)>>html.Update"%del_file, "Delete this HAR refinement")

      if os.path.exists(self.jobs[i].result_fn):
        d['link'] = "<a href='reap \"%(job_result_filename)s\"'>" %d
      else:
        d['link'] = ""

      rv += get_template('job_line')%d
    rv += "</table>"
    rv += get_template('recent_jobs', path=p_path)
    return rv

  def view_all(self):
    olx.Shell(self.jobs_dir)

  def available(self):
    return os.path.exists(self.exe)

  def getAnalysisPlotData(input_f):
    f = open(input_f, 'r').read()
    d = {}
    import re

    regex_l = [
      (r'Labelled QQ plot\:\n\n(.*?)(?:\n\n|\Z)','QQ'),
      (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Fz vs sin(theta)/lambda'),
      (r'Scatter plot of Delta F \= \(Fexp\-Fpred\) vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Delta Fz vs sin(theta)/lambda'),
      (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs Fexp \:\n\n(.*?)(?:\n\n|\Z)','Fz vs Fexp'),
    ]


    for regex_t,name in regex_l:
      regex = re.compile(regex_t, re.DOTALL)
      xs = []
      ys = []
      text = []
      m=regex.findall(f)
      if m:
        mm = ""
        for _ in m:
          if len(_) < 10:
            continue
          else:
            mm = _
        if not mm:
          print "No Data"
          continue
        raw_data = mm.strip()
        raw_data = raw_data.split("\n")
        for pair in raw_data:
          pair = pair.strip()
          if not pair:
            continue
          xs.append(float(pair.split()[0].strip()))
          ys.append(float(pair.split()[1].strip()))
          try:
            text.append("%s %s %s" %(pair.split()[2], pair.split()[3], pair.split()[4]))
          except:
            text.append("")
        d[name] = {}
        d[name].setdefault('title', name)
        d[name].setdefault('xs', xs)
        d[name].setdefault('ys', ys)
        d[name].setdefault('text', text)
      else:
        print "Could not evaluate REGEX %s." %repr(regex_t)


    makePlotlyGraph(d)



  def makePlotlyGraph(d):

    try:
      import plotly
      print plotly.__version__  # version >1.9.4 required
      from plotly.graph_objs import Scatter, Layout
      import numpy as np
      import plotly.plotly as py
      import plotly.graph_objs as go
    except:
      print "Please install plot.ly for python!"
      return

    data = []
    print len(d)
    for trace in d:
      _ = go.Scatter(
        x = d[trace]['xs'],
        y = d[trace]['ys'],
        text = d[trace]['text'],
        mode = 'markers',
        name = d[trace]['title']
        )
      data.append(_)

      layout = go.Layout(
          title='HAR Result',
          xaxis=dict(
              title='x Axis',
              titlefont=dict(
                  family='Courier New, monospace',
                  size=18,
                  color='#7f7f7f'
              )
          ),
          yaxis=dict(
              title='y Axis',
              titlefont=dict(
                  family='Courier New, monospace',
                  size=18,
                  color='#7f7f7f'
              )
          )
      )


    fig = go.Figure(data=data, layout=layout)
    plot_url = plotly.offline.plot(fig, filename='basic-line')




def getAnalysisPlotData(input_f):
  f = open(input_f, 'r').read()
  d = {}
  import re

  regex_l = [
    (r'Labelled QQ plot\:\n\n(.*?)(?:\n\n|\Z)','QQ'),
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Fz vs sin(theta)/lambda'),
    (r'Scatter plot of Delta F \= \(Fexp\-Fpred\) vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Delta Fz vs sin(theta)/lambda'),
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs Fexp \:\n\n(.*?)(?:\n\n|\Z)','Fz vs Fexp'),
  ]


  for regex_t,name in regex_l:
    regex = re.compile(regex_t, re.DOTALL)
    xs = []
    ys = []
    text = []
    m=regex.findall(f)
    if m:
      mm = ""
      for _ in m:
        if len(_) < 10:
          continue
        else:
          mm = _
      if not mm:
        print "No Data"
        continue
      raw_data = mm.strip()
      raw_data = raw_data.split("\n")
      for pair in raw_data:
        pair = pair.strip()
        if not pair:
          continue
        xs.append(float(pair.split()[0].strip()))
        ys.append(float(pair.split()[1].strip()))
        try:
          text.append("%s %s %s" %(pair.split()[2], pair.split()[3], pair.split()[4]))
        except:
          text.append("")
      d[name] = {}
      d[name].setdefault('title', name)
      d[name].setdefault('xs', xs)
      d[name].setdefault('ys', ys)
      d[name].setdefault('text', text)
    else:
      print "Could not evaluate REGEX %s." %repr(regex_t)


  makePlotlyGraph(d)



def makePlotlyGraph(d):

  try:
    import plotly
    print plotly.__version__  # version >1.9.4 required
    from plotly.graph_objs import Scatter, Layout
    import numpy as np
    import plotly.plotly as py
    import plotly.graph_objs as go
  except:
    print "Please install plot.ly for python!"
    return

  data = []
  print len(d)
  for trace in d:
    _ = go.Scatter(
      x = d[trace]['xs'],
      y = d[trace]['ys'],
      text = d[trace]['text'],
      mode = 'markers',
      name = d[trace]['title']
      )
    data.append(_)

    layout = go.Layout(
        title='HAR Statistics',
        xaxis=dict(
            title='x Axis',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
            title='y Axis',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        )
    )


  fig = go.Figure(data=data, layout=layout)
  plot_url = plotly.offline.plot(fig, filename='basic-line')


class Job(object):
  def __init__(self, parent, name):
    self.parent = parent
    self.status = 0
    self.name = name
    full_dir = os.path.join(parent.jobs_dir, self.name)
    self.full_dir = full_dir
    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.result_fn = os.path.join(full_dir, name) + ".archive.cif"
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    self.dump_fn = os.path.join(full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(full_dir, "stdout.fit_analysis")
    self.completed = os.path.exists(self.result_fn)
    initialised = False

  def save(self):
    with open(os.path.join(self.full_dir, "job.options"), "w") as f:
      for k, v in HARp_instance.options.iteritems():
        val = olx.GetVar(k, None)
        if val is not None:
          f.write("%s: %s\n" %(k, val))

  def load(self):
    options_fn = os.path.join(self.full_dir, "job.options")
    if os.path.exists(options_fn):
      self.date = os.path.getctime(self.full_dir)
      try:
        with open(options_fn, "r") as f:
          for l in f:
            l = l.strip()
            if not l or ':' not in l: continue
            toks = l.split(':')
            olx.SetVar(toks[0], toks[1])
        return True
      except:
        return False
    return False

  def launch(self):
    autorefine = olx.GetVar("settings.tonto.HAR.autorefine", None)
    if autorefine == 'true':
      olex.m("refine")
    if olx.xf.latt.IsGrown() == 'true':
      if olx.Alert("Please confirm",\
    """This is a grown structure. If you have created a cluster of molecules, make sure
    that the structure you see on the screen obeys the crystallographic symmetry.
    If this is not the case, the HAR will not work properly. Continue?""", "YN", False) == 'N':
        return
    elif olx.xf.au.GetZprime() != '1':
      olx.Grow()
      olex.m("grow -w")
    if os.path.exists(self.full_dir):
      self.backup = os.path.join(self.full_dir, "backup")
      i = 1
      while (os.path.exists(self.backup + "_%d"%i)):
        i = i + 1
      self.backup = self.backup + "_%d"%i
      os.mkdir(self.backup)
      import shutil
      try:
        files = (file for file in os.listdir(os.path.join(self.full_dir))
                 if os.path.isfile(os.path.join(self.full_dir, file)))
        for f in files:
          f_work = os.path.join(self.full_dir,f)
          f_dist = os.path.join(self.backup,f)
          shutil.move(f_work,f_dist)
      except:
        pass
    try:
      os.mkdir(self.full_dir)
    except:
      pass
    tries = 0
    while not os.path.exists(self.full_dir) and tries < 5:
      try:
        os.mkdir(self.full_dir)
        break
      except:
        time.sleep(0.1)
        tries += 1
        pass

    model_file_name = os.path.join(self.full_dir, self.name) + ".cif"
    olx.Kill("$Q")
    olx.File(model_file_name)

    data_file_name = os.path.join(self.full_dir, self.name) + ".hkl"
    if not os.path.exists(data_file_name):
      from cctbx_olex_adapter import OlexCctbxAdapter
      from iotbx.shelx import hklf
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
        for j, h in enumerate(f_sq_obs.indices()):
          s = f_sq_obs.sigmas()[j]
          if s <= 0: f_sq_obs.sigmas()[j] = 0.01
          i = f_sq_obs.data()[j]
          if i < 0: f_sq_obs.data()[j] = 0
        f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
    self.save()

    args = [self.parent.exe, self.name+".cif",
            "-basis-dir", self.parent.basis_dir,
             "-shelx-f2", self.name+".hkl"]

    disp = olx.GetVar("settings.tonto.HAR.dispersion", None)
    if 'true' == disp:
      import olexex
      from cctbx.eltbx import henke
      olex_refinement_model = OV.GetRefinementModel(False)
      sfac = olex_refinement_model.get('sfac')
      fp_fdps = {}
      wavelength = olex_refinement_model['exptl']['radiation']
      if sfac is not None:
        for element, sfac_dict in sfac.iteritems():
          custom_fp_fdps.setdefault(element, sfac_dict['fpfdp'])
      asu = olex_refinement_model['aunit']
      for residue in asu['residues']:
        for atom in residue['atoms']:
          element_type = atom['type']
          if element_type not in fp_fdps:
            fpfdp = henke.table(str(element_type)).at_angstrom(wavelength).as_complex()
            fp_fdps[element_type] = (fpfdp.real, fpfdp.imag)
      disp_arg = " ".join(["%s %s %s" %(k, v[0], v[1]) for k,v in fp_fdps.iteritems()])
      args.append("-dispersion")
      args.append('%s' %disp_arg)

    for k,v in HARp_instance.options.iteritems():
      val = olx.GetVar(k, None)
      if len(v) == 2:
        if val is not None:
          args.append('-' + v[1])
          args.append(val)
      elif k == 'settings.tonto.HAR.hydrogens':
        if val == 'positions only':
          args.append("-h-adps")
          args.append("f")
        elif val == 'positions+Uiso':
          args.append("-h-adps")
          args.append("f")
          args.append("-h-iso")
          args.append("t")
        elif val == "positions+Uaniso":
          args.append("-h-adps")
          args.append("t")
        elif val == "leave_alone":
          args.append("-h-adps")
          args.append("f")
          args.append("-h-iso")
          args.append("f")
          args.append("-h-pos")
          args.append("f")
        pass

    os.environ['hart_cmd'] = '+&-'.join(args)
    os.environ['hart_file'] = self.name
    os.environ['hart_dir'] = self.full_dir
    from subprocess import Popen
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      retur
    Popen([pyl,
           os.path.join(olx.BaseDir(), "util", "pyUtil", "PyToolLib", "HARt-launch.py")])


def del_dir(directory):
  import shutil
  shutil.rmtree(directory)


HARp_instance = HARp()
OV.registerFunction(HARp_instance.available, False, "tonto.HAR")
OV.registerFunction(HARp_instance.list_jobs, False, "tonto.HAR")
OV.registerFunction(HARp_instance.view_all, False, "tonto.HAR")
OV.registerFunction(HARp_instance.launch, False, "tonto.HAR")
OV.registerFunction(HARp_instance.getBasisListStr, False, "tonto.HAR")
OV.registerFunction(getAnalysisPlotData, False, "tonto.HAR")
OV.registerFunction(makePlotlyGraph, False, "tonto.HAR")
OV.registerFunction(del_dir, False, "tonto.HAR")
print "OK."
