import argparse
import random
from pathlib import Path
from typing import Optional, NamedTuple


class Split(NamedTuple):
    training: list[Path]
    validation: list[Path]



def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'directory', type=str,
        help='Base directory file directory. Elements are collected from here.'
    )
    parser.add_argument('savedirectory', type=str,
                        help='Indicate the directory where the fold text files will be saved. '
                             'Be aware: Preexisting files will be overwritten!')
    parser.add_argument('-f', '--folds', type=int, default=1,
                        help='Number of folds.')
    parser.add_argument('-s', '--suffix', type=str, default=None,
                        help='Filter for subset of files that have the given suffix.')
    parser.add_argument('-v', '--validation-size', type=int,
                        help='Number of validation dataset instances.')
    args = parser.parse_args()
    return args


def collect_matching_filepaths(directory: Path, suffix: Optional[str] = None) -> list[Path]:
    files = list(filter(lambda f: f.is_file(), directory.iterdir()))
    if suffix:
        if not suffix.startswith('.'):
            suffix = ''.join(('.', suffix))
        files = [f for f in files if f.suffix == suffix]
    return files


def sample_files(files: list[Path],
                 folds: int, validation_size: int) -> Split:
    if len(files) < (folds * validation_size):
        message = (f'Combined set size (N={folds*validation_size}) of validation folds '
                   f'exceeds total number of eligible files (N={len(files)})')
        raise ValueError(message)

    indices = list(range(len(files)))
    validation_indices = random.sample(indices, k=(folds*validation_size))

    indices_iterator = iter(validation_indices)

    folds_validation_indices = []
    folds_training_indices = []

    for _ in range(folds):
        fold_validation_indices = {
            next(indices_iterator) for _ in range(validation_size)
        }
        fold_training_indices = set(indices) - fold_validation_indices
        folds_validation_indices.append(fold_validation_indices)
        folds_training_indices.append(fold_training_indices)

    training = [
        [files[instance_idx] for instance_idx in instance_indices]
        for instance_indices in folds_training_indices 
    ]
    validation = [
        [files[instance_idx] for instance_idx in instance_indices]
        for instance_indices in folds_validation_indices 
    ]

    return Split(training, validation)
    

def write(split: Split, directory: Path) -> None:
    training, validation = split
    for i, (trainfold, valfold) in enumerate(zip(training, validation)):
        filepath = directory / f'fold-{i}-paths.txt'
        with open(filepath, mode='w') as handle:
            handle.write('training\n')
            handle.writelines(
                (''.join(('- ', str(p), '\n')) for p in trainfold)
            )
            handle.write('\nvalidation\n')
            handle.writelines(
                (''.join(('- ', str(p), '\n')) for p in valfold)
            )




if __name__ == '__main__':
    args = cli()
    directory = Path(args.directory)
    save_directory = Path(args.savedirectory)
    files = collect_matching_filepaths(directory, args.suffix)
    split = sample_files(files, args.folds, args.validation_size)
    write(split, save_directory)
    print(f'Saved fold files to "{save_directory}"')