import json
import sys
import io
import argparse

# ------
# 'key' functions that make signatures from selected fields used to identify sample groups, etc
# ------

def find_sequence_protocol_key(sample):
    key = {
        'template_class': sample['template_class'],
        'forward_pcr_primer_target_location': [],
        'reverse_pcr_primer_target_location': [],
        'pcr_target_locus': [],
        'sequencing_platform': sample['sequencing_platform'],
        'single_cell': sample['single_cell'],
        'complete_sequences': sample['complete_sequences']
    }

    for target in sample['pcr_target']:
        for field in ['pcr_target_locus', 'forward_pcr_primer_target_location', 'reverse_pcr_primer_target_location']:
            if target[field] is not None:
                key[field].append(target[field])
    for field in ['pcr_target_locus', 'forward_pcr_primer_target_location', 'reverse_pcr_primer_target_location']:
        if len(key[field]) > 0:
            key[field] = ', '.join(key[field])
        else:
            key[field] = None

    return key


def find_tissue_processing_key(sample):
    key = {
        'cell_subset': sample['cell_subset']['label'],
        'cell_phenotype': sample['cell_phenotype'],
        'tissue': sample['tissue']['label'],
        'anatomic_site': sample['anatomic_site'],
        'cell_species': sample['cell_species']['label'],
    }

    return key


def find_sample_group_key(sample):
    key = {
        'collection_time_point_relative': sample['collection_time_point_relative'],
        'collection_time_point_reference': sample['collection_time_point_reference'],
    }

    return key


# compare two keys,
def identical_keys(key1, key2):
    if len(key1.keys()) != len(key2.keys()):
        return False

    for k in key1.keys():
        if k not in key2 or key1[k] != key2[k]:
            return False

    return True


def assign_protocol(protocols, key):
    for i in range(len(protocols)):
        if identical_keys(protocols[i]['key'], key):
            return i

    protocols.append({'key': key})
    return len(protocols) - 1


# Return string-formatted key value pairs for all non None values
def str_keys(pairs, inc_none=False, sep=', ', padding=''):
    ret = []
    for k, v in pairs.items():
        if v is not None or inc_none:
            ret.append(padding + '%s: %s' % (k, v))

    return sep.join(ret)


# ------
# output functions that honour style settings
# ------

# Write summary of ImmuneReceptor info in appropriate style
def write_narrative(text, style, fo):
    if 'NARRATIVE' in style:
        if 'VDJBASE_YAML' in style:
            text = '# ' + text

        text += '\n'
#        fo.write(text.encode("utf-8", errors='replace'))
        fo.write(text)

# Write VDJbase definitions in appropriate style
def write_vdjbase(text, style, fo):
    if 'VDJBASE_YAML' in style:
        text += '\n'
        fo.write(text)
#        fo.write(text.encode("utf-8", errors='replace'))


# ------
# functions that produce the appropriate fields for each section of the vdjbase schema
# ------

def get_pubmed_ref(pmid):
    if pmid is None:
        return 'TODO'

    if 'PMID:' in pmid:
        ref = pmid.replace('PMID:', '')
        ref = ref.replace(' ', '')
        ref = ref.split(',')[0]
        return 'https://pubmed.ncbi.nlm.nih.gov/' + ref

    elif 'DOI:' in pmid:
        ref = pmid.replace('DOI:', '')
        ref = ref.replace(' ', '')
        ref = ref.replace('\\', '')
        ref = ref.split(',')[0]
        return 'http://doi.org/' + ref

    else:
        return 'TODO'

def vdjbase_project(study, project_number):
    ret = 'P%d:\n' % project_number
    fields = {
        'Accession id': study['study_id'],
        'Accession reference': 'https://www.ncbi.nlm.nih.gov/bioproject/' + study['study_id'] if 'PRJNA' in study['study_id'] else 'TODO',
        'Contact': study['lab_name'],
        'Institute': study['lab_address'],
        'Project': 'P%d' % project_number,
        'Reference': get_pubmed_ref(study['pub_ids']),
        'Researcher': study['lab_name'],
    }

    ret += str_keys(fields, True, '\n', padding='  ')
    return ret


def vdjbase_sequence_protocol(sequence_protocol, sequence_protocol_number):
    ret = '    Sequence Protocol %d:\n' % sequence_protocol_number
    fields = {
        'Helix': sequence_protocol['template_class'],
        'Name': 'Sequence Protocol %d' % sequence_protocol_number,
        'Primer 3 location': sequence_protocol['reverse_pcr_primer_target_location'],
        'Primer 5 location': sequence_protocol['forward_pcr_primer_target_location'],
        'Sequencing_length':  sequence_protocol['complete_sequences'],
        'Sequencing_platform':  sequence_protocol['sequencing_platform'],
        'UMI': 'TODO',
    }
    ret += str_keys(fields, True, '\n', padding='      ')
    return ret


def vdjbase_tissue_processing(tissue_processing, tissue_processing_number):
    ret = '    Tissue Processing %d:\n' % tissue_processing_number
    fields = {
        'Cell Type': tissue_processing['cell_subset'],
        'Isotype': tissue_processing['cell_phenotype'],
        'Name': 'Tissue Processing %d' % tissue_processing_number,
        'Species': tissue_processing['species'],
        'Sub cell type': tissue_processing['cell_phenotype'],
        'Tissue': tissue_processing['tissue']
    }
    ret += str_keys(fields, True, '\n', padding='      ')
    return ret


def vdjbase_subject(subject, project_number, subject_number):
    ret = '    P%d_I%d:\n' % (project_number, subject_number)
    fields = {
        'Age': subject['age_min'] if subject['age'] is None else subject['age'],
        'Cohort': subject['diagnosis'][0]['study_group_description'],
        'Ethnic': subject['ethnicity'],
        'Health Status': subject['diagnosis'][0]['disease_diagnosis']['label'],
        'Name': 'P%d_I%d' % (project_number, subject_number),
        'Original name': subject['subject_id'],
        'Sex': subject['sex'],
        'Country': subject['ancestry_population'],
    }
    ret += str_keys(fields, True, '\n', padding='      ')
    return ret


def vdjbase_sample(sample, project_number, subject_number, sample_number):
    ret = '    P%d_I%d_S%d:\n' % (project_number, subject_number, sample_number)

    locus = []
    for target in sample['sample']['pcr_target']:
        if target['pcr_target_locus'] is not None:
            locus.append(target['pcr_target_locus'])
    locus = ', '.join(locus)

    fields = {
        'Chain': locus,
        'Name': 'P%d_I%d_S%d' % (project_number, subject_number, sample_number),
        'Sample Group': sample['sample_group'],
        'Sequence Protocol Name': 'Sequence Protocol %d' % sample['sequence_protocol'],
        'Subject Name': 'P%d_I%d' % (project_number, subject_number),
        'Tissue Processing Name': 'Tissue Protocol %d' % sample['tissue_processing'],
    }
    ret += str_keys(fields, True, '\n', padding='      ')
    return ret


# ------
# ------


def main():
    parser = argparse.ArgumentParser(description='Parse iReceptor metadata and convert to VDJbase format')
    parser.add_argument('input_file', help='iReceptor metadata for one or more studies (JSON)')
    parser.add_argument('-o', '--output_file', help='output from this script (if not specified, will write to standard outout)')
    parser.add_argument('-p', '--project_number', help='starting project number to use')
    parser.add_argument('-c', '--comments', help='include narrative based on iReceptor metadata', action='store_true')
    parser.add_argument('-v', '--vdjbase', help='include YAML output for VDJbase', action='store_true')
    args = parser.parse_args()

    style = []
    if args.comments:
        style.append('NARRATIVE')
    if args.vdjbase:
        style.append('VDJBASE_YAML')

    if len(style) == 0:
        print('Please use one or more flags (-c, -v) to specify the output you would like.')
        exit(0)

    if args.output_file:
        fo = open(args.output_file, 'w', errors='replace')
    else:
        sys.stdout.reconfigure(errors='replace')
        fo = sys.stdout

    if args.project_number:
        try:
            project_number = int(args.project_number)
        except:
            print('The starting project number must be an integer.')
            exit(0)
    else:
        project_number = 1

    with open(args.input_file, 'r') as fi:
        whole_doc = json.load(fi)
        rep = whole_doc['Repertoire']
        studies = {}

        for study in rep:
            title = study['study']['study_title']
            if title not in studies:
                studies[title] = {'subjects': {}, 'sequence_protocols': [], 'tissue_processing': [], 'sample_groups': [], 'study': study['study'], 'species': study['subject']['species']['label']}
            subject_id = study['subject']['subject_id']
            if subject_id not in studies[title]['subjects']:
                studies[title]['subjects'][subject_id] = {'samples': [], 'subject': study['subject']}

            for sample in study['sample']:
                sequence_protocol_key = find_sequence_protocol_key(sample)
                sequence_protocol_index = assign_protocol(studies[title]['sequence_protocols'], sequence_protocol_key)
                tissue_processing_key = find_tissue_processing_key(sample)
                tissue_processing_key['species'] = studies[title]['species']
                tissue_processing_index = assign_protocol(studies[title]['tissue_processing'], tissue_processing_key)
                sample_group_key = find_sample_group_key(sample)
                sample_group_index = assign_protocol(studies[title]['sample_groups'], sample_group_key)

                studies[title]['subjects'][subject_id]['samples'].append({
                    'sequence_protocol': sequence_protocol_index,
                    'tissue_processing': tissue_processing_index,
                    'sample_group': sample_group_index,
                    'sample': sample,
                    'sample_id': sample['sample_id'],
                    'sample_processing_id': sample['sample_processing_id'],
                    'sequencing_run_id': sample['sequencing_run_id'],
                    'sequencing_file': sample['sequencing_files']['filename']
                        })

        for title, study in studies.items():
            sample_fo = io.StringIO()           # buffer up sample lines so we can emit after other blocks

            write_narrative('Study: %s' % title, style, fo)
            write_vdjbase(vdjbase_project(study['study'], project_number), style, fo)
            project_number += 1

            write_vdjbase('  Sequence Protocol:', style, fo)
            for i in range(len(study['sequence_protocols'])):
                write_narrative('   Sequence Protocol %d: %s' % (i, str_keys(study['sequence_protocols'][i]['key'])), style, fo)
                write_vdjbase(vdjbase_sequence_protocol(study['sequence_protocols'][i]['key'], i), style, fo)

            write_vdjbase('  Tissue Processing:', style, fo)
            for i in range(len(study['tissue_processing'])):
                write_narrative('   Tissue Processing %d: %s' % (i, str_keys(study['tissue_processing'][i]['key'])), style, fo)
                write_vdjbase(vdjbase_tissue_processing(study['tissue_processing'][i]['key'], i), style, fo)

            for i in range(len(study['sample_groups'])):
                write_narrative('   Sample Groups %d: %s' % (i, str_keys(study['sample_groups'][i]['key'])), style, fo)

            subject_number = 1
            fo.write('  Subjects:\n')
            for subject, detail in study['subjects'].items():
                # work out which detail fields don't vary across samples
                unvarying = []
                if len(detail['samples']) > 1:
                    fields = detail['samples'][0].keys()
                    for field in fields:
                        if field != 'sample':
                            values = {}
                            for sample in detail['samples']:
                                if sample[field] is not None:
                                    values[sample[field]] = 1
                            if len(values) == 1:
                                unvarying.append(field)

                unvaried = []

                for k in unvarying:
                    unvaried.append('%s: %s' % (k, detail['samples'][0][k]))

                unvaried = '(%s)' % ', '.join(unvaried) if len(unvaried) > 0 else ''

                write_narrative('   Subject: %s %s' % (subject, unvaried), style, fo)
                write_vdjbase(vdjbase_subject(detail['subject'], project_number, subject_number), style, fo)
                subject_number += 1

                sample_number = 1
                for sample in detail['samples']:
                    details = []
                    for k, v in sample.items():
                        if v is not None and k not in unvarying and k != 'sample':
                            details.append('%s: %s' % (k, v))
                    write_narrative('      %s' % ', '.join(details), style, sample_fo)
                    write_vdjbase(vdjbase_sample(sample, project_number, subject_number, sample_number), style, sample_fo)
                    sample_number += 1

            fo.write('  Samples:\n')
            fo.write(sample_fo.getvalue())
            sample_fo.close()


if __name__ == "__main__":
    main()
