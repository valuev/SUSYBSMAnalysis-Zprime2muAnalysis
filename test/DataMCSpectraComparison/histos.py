#!/usr/bin/env python

import sys, os, FWCore.ParameterSet.Config as cms
from SUSYBSMAnalysis.Zprime2muAnalysis.Zprime2muAnalysis_cfg import process
from SUSYBSMAnalysis.Zprime2muAnalysis.HistosFromPAT_cfi import HistosFromPAT
from SUSYBSMAnalysis.Zprime2muAnalysis.VBTFSelection_cff import vbtf_loose, vbtf_tight
from SUSYBSMAnalysis.Zprime2muAnalysis.PATCandViewShallowCloneCombiner_cfi import allDimuons as plainDimuons

# CandCombiner includes charge-conjugate decays with no way to turn it
# off. To get e.g. mu+mu+ separate from mu-mu-, cut on the sum of the
# pdgIds (= -26 for mu+mu+).
common_dil_cut = '' #daughter(0).momentum.Dot(daughter(1).momentum())/daughter(0).momentum().Mag()/daughter(1).momentum().Mag() > 0.02'
dils = [
    ('MuonsPlusMuonsMinus',          '%(leptons_name)s:muons@+ %(leptons_name)s:muons@-',         'daughter(0).pdgId() + daughter(1).pdgId() == 0'),
    ('MuonsPlusMuonsPlus',           '%(leptons_name)s:muons@+ %(leptons_name)s:muons@+',         'daughter(0).pdgId() + daughter(1).pdgId() == -26'),
    ('MuonsMinusMuonsMinus',         '%(leptons_name)s:muons@- %(leptons_name)s:muons@-',         'daughter(0).pdgId() + daughter(1).pdgId() == 26'),
    ('MuonsSameSign',                '%(leptons_name)s:muons@- %(leptons_name)s:muons@-',         ''),
    ('ElectronsPlusElectronsMinus',  '%(leptons_name)s:electrons@+ %(leptons_name)s:electrons@-', 'daughter(0).pdgId() + daughter(1).pdgId() == 0'),
    ('ElectronsPlusElectronsPlus',   '%(leptons_name)s:electrons@+ %(leptons_name)s:electrons@+', 'daughter(0).pdgId() + daughter(1).pdgId() == -22'),
    ('ElectronsMinusElectronsMinus', '%(leptons_name)s:electrons@- %(leptons_name)s:electrons@-', 'daughter(0).pdgId() + daughter(1).pdgId() == 22'),
    ('ElectronsSameSign',            '%(leptons_name)s:electrons@- %(leptons_name)s:electrons@-', ''),
    ('MuonsPlusElectronsMinus',      '%(leptons_name)s:muons@+ %(leptons_name)s:electrons@-',     'daughter(0).pdgId() + daughter(1).pdgId() == -2'),
    ('MuonsMinusElectronsPlus',      '%(leptons_name)s:muons@- %(leptons_name)s:electrons@+',     'daughter(0).pdgId() + daughter(1).pdgId() == 2'),
    ('MuonsPlusElectronsPlus',       '%(leptons_name)s:muons@+ %(leptons_name)s:electrons@+',     'daughter(0).pdgId() + daughter(1).pdgId() == -24'),
    ('MuonsMinusElectronsMinus',     '%(leptons_name)s:muons@- %(leptons_name)s:electrons@-',     'daughter(0).pdgId() + daughter(1).pdgId() == 24'),
    ('MuonsElectronsOppSign',        '%(leptons_name)s:muons@+ %(leptons_name)s:electrons@-',     ''),
    ('MuonsElectronsSameSign',       '%(leptons_name)s:muons@+ %(leptons_name)s:electrons@+',     ''),
    ]

# Define groups of cuts to make the plots for.
cuts = [
# If adding these other cuts back in, hltFilter needs to be added in the below.
#    ('Pt20', 'isGlobalMuon && pt > 20'), 
#    ('Std',  'isGlobalMuon && pt > 20 && isolationR03.sumPt < 10'),
    ('VBTF', 'isGlobalMuon && pt > 20'),
    ('VBTFwoEta', 'isGlobalMuon && pt > 20'),
    ('VBTFwoIso', 'isGlobalMuon && pt > 20'),
    ('VBTFwB2B', 'isGlobalMuon && pt > 20'),
    ('VBTFwVtxProb', 'isGlobalMuon && pt > 20'),
    ]

simple_ntuple = False

for cut_name, muon_cuts in cuts:
    #if cut_name != 'VBTF': continue
    
    # Keep track of modules to put in the path for this set of cuts.
    path_list = []

    # Clone the LeptonProducer to make leptons with the set of cuts
    # we're doing here flagged.
    leptons_name = cut_name + 'Leptons'
    leptons = process.leptons.clone(muon_cuts = muon_cuts)
    setattr(process, leptons_name, leptons)
    path_list.append(leptons)

    # Make all the combinations of dileptons we defined above.
    for dil_name, dil_decay, dil_cut in dils:
        #if dil_name != 'MuonsPlusMuonsMinus': continue

        name = cut_name + dil_name
        allname = 'all' + name

        if common_dil_cut and dil_cut:
            dil_cut = common_dil_cut + ' && (%s)' % dil_cut

        alldil = process.allDimuons if 'VBTF' in cut_name else plainDimuons
        alldil = alldil.clone(decay = dil_decay % locals(), cut = dil_cut)
        dil = process.dimuons.clone(src = cms.InputTag(allname))

        if 'woEta' in cut_name:
            alldil.loose_cut = vbtf_loose.replace('abs(eta) < 2.4 && ', '')
            alldil.tight_cut = vbtf_tight.replace('abs(eta) < 2.1 && ', '')
            alldil.tight_cut = vbtf_tight.replace('abs(triggerObjectMatchesByPath("HLT_Mu9").at(0).eta()) < 2.1 && ', '')
            alldil.tight_cut = vbtf_tight.replace('abs(triggerObjectMatchesByPath("HLT_Mu11").at(0).eta()) < 2.1 && ', '')
        elif 'woIso' in cut_name:
            alldil.loose_cut = vbtf_loose.replace('isolationR03.sumPt < 3 && ', '')
        elif 'wB2B' in cut_name:
            dil.back_to_back_cos_angle_min = 0.02
        elif 'wVtxProb' in cut_name:
            dil.vertex_chi2_max = 10

        histos = HistosFromPAT.clone(lepton_src = cms.InputTag(leptons_name, 'muons'), dilepton_src = cms.InputTag(name))

        setattr(process, allname, alldil)
        setattr(process, name, dil)
        setattr(process, name + 'Histos', histos)
        path_list.append(alldil * dil * histos)

        if simple_ntuple:
            SimpleNtupler = cms.EDAnalyzer('SimpleNtupler', hlt_src = cms.InputTag('TriggerResults', '', 'HLT'), dimu_src = cms.InputTag(name))
            setattr(process, name + 'SimpleNtupler', SimpleNtupler)
            path_list[-1] *= SimpleNtupler

    # Finally, make the path for this set of cuts. Don't use hltFilter
    # here, but rely on the VBTF selection to take care of it -- easy
    # way to handle the changing trigger names.
    pathname = 'path' + cut_name
    path = cms.Path(process.goodDataFilter * process.muonPhotonMatch * reduce(lambda x,y: x*y, path_list))
    setattr(process, pathname, path)

if 'data' in sys.argv:
    # "daata" since otherwise crab tries to pack up that dir and send
    # it off to the worker nodes...
    process.source.fileNames = ['file:work/daata/jul15.root', 'file:work/daata/prompt.root']
    process.GlobalTag.globaltag = 'GR10_P_V7::All'
    process.TFileService.fileName = 'ana_datamc_data.root'

    #process.ppp = cms.EDAnalyzer('PrintAbove110', src = cms.InputTag('VBTFMuonsPlusMuonsMinus'), above = cms.double(50))
    #process.pathVBTF *= process.ppp

if __name__ == '__main__' and 'submit' in sys.argv:
    crab_cfg = '''
[CRAB]
jobtype = cmssw
scheduler = condor

[CMSSW]
datasetpath = %(ana_dataset)s
dbs_url = https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet
pset = histos_crab.py
get_edm_output = 1
total_number_of_events = -1
events_per_job = 20000

[USER]
ui_working_dir = crab/crab_ana_datamc_%(name)s
return_data = 1
'''

    from samples import samples
    for sample in samples:
        print sample.name

        new_py = open('histos.py').read()
        new_py += "\nprocess.hltFilter.TriggerResultsTag = cms.InputTag('TriggerResults', '', '%(hlt_process_name)s')\n" % sample
        open('histos_crab.py', 'wt').write(new_py)

        open('crab.cfg', 'wt').write(crab_cfg % sample)
        os.system('crab -create -submit all')

    os.system('rm crab.cfg histos_crab.py')