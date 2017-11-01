for SMMART 

[walsbr@exalab3 SMMARTData]$ find . -name LIB170201PS_TB78_Buffy_S1_R1_001.fastq.gz -print
./Patients/16113-101/fastq/LIB170201PS_TB78_Buffy_S1_R1_001.fastq.gz
./DataTransfer/170202_NS500681_0097_AHK2M3BGXY/fastq/LIB170201PS/LIB170201PS_TB78_Buffy_S1_R1_001.fastq.gz
find: `./Germline/RNA170210CC': Permission denied
./ForBackup/170202_NS500681_0097_AHK2M3BGXY/fastq/LIB170201PS/LIB170201PS_TB78_Buffy_S1_R1_001.fastq.gz


ignore the **/DataTransfer directory
use the md5sum.txt found in /ForBackup
16113-101  = `Patient ID` patient_id
LIB170201PS_TB78_Buffy = `Library ID` library_id


