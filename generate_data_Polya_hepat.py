import sys
sys.path = ["/mnt/storage/home/vsfishman/.local/lib/python3.5/site-packages"] + sys.path
import logging
from ChiPSeqReader import ChiPSeqReader
from Contacts_reader import ContactsReader
from RNASeqReader import RNAseqReader
from E1_Reader import E1Reader,fileName2binsize
from shared import Interval, Parameters
from DataGenerator import generate_data
from PredictorGenerators import E1PredictorGenerator,ChipSeqPredictorGenerator, \
                SmallChipSeqPredictorGenerator,SmallE1PredictorGenerator, \
                SitesOrientPredictorGenerator, OrientBlocksPredictorGenerator
from VectPredictorGenerators import loopsPredictorGenerator
from LoopReader import LoopReader
import pandas as pd
import os


if __name__ == '__main__': #Requered for parallization, at least on Windows
    #,"chr10", "chr1"]:
    for conttype in ["contacts.gz","oe.gz"]:
        logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', datefmt='%I:%M:%S', level=logging.DEBUG)

        input_folder ="input/Hepat/"
        #output_folder = "D:/Users/Polina/3Dpredictor/"
        output_folder = "out/Hepat/validating_chrms/"
        #input_folder =  "input"

        params = Parameters()
        params.window_size = 25000 #region around contact to be binned for predictors
        #params.small_window_size = 12500 #region  around contact ancors to be considered as cis
        params.mindist = 50001 #minimum distance between contacting regions
        #params.maxdist = params.window_size #max distance between contacting regions
        params.maxdist = 1500000
        #params.binsize = 20000 #when binning regions with predictors, use this binsize
        params.sample_size = 25000 #how many contacts write to file
        #params.conttype = "oe.gz"
        params.conttype = conttype
        params.max_cpus = 12

        logging.getLogger(__name__).debug("Using input folder "+input_folder)

        #Read contacts data
        params.contacts_reader = ContactsReader()
        contacts_files = []
        contacts_files=[input_folder+ "chr"+str(i)+".5MB.Hepat."+params.conttype for i in range(1,20)]
        contacts_files.append(input_folder+ "chrX.5MB.Hepat."+params.conttype)
        params.contacts_reader.read_files(contacts_files)
        #
        # #Loops predictor
        # loopsReader = LoopReader("input/Hepat.merged.loops")
        # loopsReader.read_loops()
        # loopspg = loopsPredictorGenerator(loopsReader, params.window_size)

        # Read CTCF data
        logging.info('create CTCF_PG')
        params.ctcf_reader = ChiPSeqReader(input_folder + "CTCF/Hepat_WT_MboI_rep1-rep2.IDR0.05.filt.narrowPeak.gz",
                                                            name="CTCF")
        params.ctcf_reader.read_file()
        params.ctcf_reader.set_sites_orientation(
            input_folder + "CTCF/Hepat_WT_MboI_rep1-rep2_IDR0_05_filt_narrowPeak-orient_N10.bed.gz")


        OrientCtcfpg = SitesOrientPredictorGenerator(params.ctcf_reader,
                                                     N_closest=4)
        NotOrientCTCFpg = SmallChipSeqPredictorGenerator(params.ctcf_reader,
                                                         params.window_size,
                                                         N_closest=4)

        # Read CTCF data and drop sites w/o known orientation
        params.ctcf_reader_orientOnly = ChiPSeqReader(input_folder + "CTCF/Hepat_WT_MboI_rep1-rep2.IDR0.05.filt.narrowPeak.gz",
                                                            name="CTCF")
        params.ctcf_reader_orientOnly.read_file()
        params.ctcf_reader_orientOnly.set_sites_orientation(
            input_folder + "CTCF/Hepat_WT_MboI_rep1-rep2_IDR0_05_filt_narrowPeak-orient_N10.bed.gz")
        params.ctcf_reader_orientOnly.keep_only_with_orient_data()
        OrientBlocksCTCFpg = OrientBlocksPredictorGenerator(params.ctcf_reader_orientOnly,
                                                             params.window_size)

        # #Read other chip-seq data
        # logging.info('create chipPG')
        # chipPG = []
        # filenames_df = pd.read_csv(input_folder + "peaks/filenames.csv")
        # assert len(os.listdir(input_folder + 'peaks/')) - 1 == len(filenames_df['name'])
        # # print(len(os.listdir(input_folder + 'peaks/')))
        # # print(len(filenames_df['name']))
        # for index, row in filenames_df.iterrows():
        #     params.chip_reader = ChiPSeqReader(input_folder + 'peaks/' + row["filename"] + '.gz', name=row['name'])
        #     params.chip_reader.read_file()
        #     chipPG.append(SmallChipSeqPredictorGenerator(params.chip_reader,params.window_size,N_closest=4))
        #
        # #Read methylation data
        # logging.info('create metPG')
        # metPG = []
        # filemanes_df = pd.read_csv(input_folder + "methylation/filenames.csv")
        # assert len(os.listdir(input_folder + 'peaks/')) - 1 == len(filenames_df['name'])
        # for index, row in filemanes_df.iterrows():
        #     #print(row["name"])
        #     params.met_reader = ChiPSeqReader(input_folder + 'methylation/'+ row["filename"], name=row['name'])
        #     params.met_reader.read_file(renamer={"0":"chr","1":"start","2":"end","4":"sigVal"})
        #     metPG.append(SmallChipSeqPredictorGenerator(params.met_reader,params.window_size,N_closest=4))
        # #Read cage data
        # cagePG = []
        # filemanes_df = pd.read_csv(input_folder + "cage/filenames.csv")
        # assert len(os.listdir(input_folder + 'peaks/')) - 1 == len(filenames_df['name'])
        # for index, row in filemanes_df.iterrows():
        #     #print(row["name"])
        #     params.cage_reader = ChiPSeqReader(input_folder + 'cage/' + row["filename"], name=row['name'])
        #     params.cage_reader.read_file(renamer={"0":"chr","1":"start","2":"end","4":"sigVal"})
        #     cagePG.append(SmallChipSeqPredictorGenerator(params.cage_reader,params.window_size,N_closest=4))
        # Read RNA-Seq data
        params.RNAseqReader = RNAseqReader(fname=input_folder+"RNA/GSE95111_genes.fpkm_table.txt.pre.txt",
                                           name="RNA")
        params.RNAseqReader.read_file(rename={"Gene name": "gene",
                                              "Gene start (bp)": "start",
                                              "Gene end (bp)": "end",
                                              "Chromosome/scaffold name": "chr",
                                              "shCtrl-1_0": "sigVal"},
                                      sep="\t")
        RNAseqPG = SmallChipSeqPredictorGenerator(params.RNAseqReader,
                                                  window_size=params.window_size,
                                                  N_closest=3)

        #Read E1 data
        params.eig_reader = E1Reader()
        params.eig_reader.read_files([input_folder + "chr1.Hepat.E1.50k",
                               input_folder + "chr2.Hepat.E1.50k",
                               input_folder + "chr10.Hepat.E1.50k"],
                               #input_folder + "chr6.Hepat.E1.50k"],
                              binSizeFromName=fileName2binsize) #infer size of E1 bins from file name using this function

        e1pg = SmallE1PredictorGenerator(params.eig_reader,params.window_size)

        params.pgs = [OrientCtcfpg, NotOrientCTCFpg, OrientBlocksCTCFpg, RNAseqPG] #+ metPG + chipPG + cagePG

        # # Generate train
        # for trainChrName in ["chr10", "chr2"]:
        #     training_file_name = "2018-10-23-training.RandOn" + trainChrName + str(params) + ".txt"
        #     params.interval = Interval(trainChrName,
        #                           params.contacts_reader.get_min_contact_position(trainChrName),
        #                           params.contacts_reader.get_max_contact_position(trainChrName))
        #     params.out_file = output_folder + training_file_name
        #     generate_data(params,saveFileDescription=True)
        #     del(params.out_file)

        #Generate test
        # for interval in [# Interval("chr10", 59000000, 62000000)]:
        #                  Interval("chr10", 65000000, 70000000),
        #                  Interval("chr20", 37000000, 40000000),
        #                  Interval("chr10", 10000000, 60000000)]:
        #                  # Interval("chr10",36000000,41000000),
        #                  # Interval("chr1", 100000000, 110000000)]:
        # params.interval = interval
        validate_chrs=["chr19", "chrX"]
        for validateChrName in validate_chrs:
            params.sample_size = len(params.contacts_reader.data[validateChrName])
            #print(params.sample_size)
            validation_file_name = "validatingOrient." + str(params) + ".txt"
            params.interval = Interval(validateChrName,
                                       params.contacts_reader.get_min_contact_position(validateChrName),
                                       params.contacts_reader.get_max_contact_position(validateChrName))
            logging.getLogger(__name__).info("Generating validation dataset for interval "+str(params.interval))
            params.out_file = output_folder + params.interval.toFileName() + validation_file_name
            generate_data(params)
            del(params.out_file)
            del (params.sample_size)

        # for object in [params.contacts_reader]+params.pgs:
        #     lostInterval = Interval("chr1",103842568,104979840)
        #     object.delete_region(lostInterval)
        #     params.interval = Interval("chr1",100000000,109000000)
        #     logging.getLogger(__name__).info("Saving data to file "+params.interval.toFileName() + "DEL." + lostInterval.toFileName()+validation_file_name)
        # params.out_file = params.interval.toFileName() + "DEL." + lostInterval.toFileName()+validation_file_name
        # generate_data(params)