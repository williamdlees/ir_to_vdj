# ir_to_vdj - a script to parse iReceptor gateway metadata, and convert to VDJbase format

## Usage

```
usage: python ir_to_vdj.py [-h] [-o OUTPUT_FILE] [-p PROJECT_NUMBER] [-c] [-v] input_file

Parse iReceptor metadata and convert to VDJbase format

positional arguments:
  input_file            iReceptor metadata for one or more studies (JSO N)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        output from this script (if not specified, will write to standard outout)
  -p PROJECT_NUMBER, --project_number PROJECT_NUMBER
                        starting project number to use
  -c, --comments        include narrative based on iReceptor metadata
  -v, --vdjbase         include YAML output for VDJbase```
```

The input file should contain iReceptor gateway metadata for one or more studies, in JSON format. To produce this:
* log in to [iReceptor](https://gateway.ireceptor.org)
* click on 'Browse Repertoire Metadata'
* use the filters to select the studies you want
* click on 'download JSON'

Example json files are available in this repo.

-c produces a condensed summary of the iReceptor metadata which can be useful for initial review [example](PRJNA260556-c.txt).

-v produces the vdjbase metadata [example](PRJNA260556-v.yml).

The two can be combined to provide vdjbase metadata with the sumamry as comments. This will facilitate review of the converted metadata [example](PRJNA260556-v-c.yml).

## Limitations

Use of fields in the two formats is not precisely equivalent. The output file will need careful review to confirm that it matches VDJBase expectations.

In some cases, where ir_to_vdj is unable to translate a field, it will insert the string TODO in the output. The output file should be searched for TODO.

iReceptor does not have a concept of sample groups, sequence processing groups or tissue processing groups. ir_to_vdj attempts to infer these by 
gathering samples that have identical values in relevant fields. The identified groups should be reviewed and modified if necessary.
Note that sample groups are not explicitly described in VDJbase metadata, although each sample indicates the group
it belongs to. The inferred groups are listed in the comments produced by the -c option.

iReceptor does not identify whether UMI barcodes are used in sequencing. The Sequence Protocol field UMI will always
be set to TODO and will need to be updated during review.

The script was tested with python 3.9. It will probably work with earlier versions of python 3.


