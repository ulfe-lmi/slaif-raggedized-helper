"""Fixed random toy generation child. Never import from the application process."""
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys


def write_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
    path.chmod(0o600)


def generate(target):
    # This function is dispatched only after the external source gate and permit.
    sys.path.insert(0, '/packages')
    pins = {'torch': '2.10.0+cpu', 'transformers': '4.51.3', 'tokenizers': '0.21.4',
            'safetensors': '0.5.3', 'huggingface-hub': '0.30.2', 'numpy': '2.2.6'}
    if sys.version_info[:3] != (3, 12, 15):
        raise ValueError('runtime mismatch')
    if any(importlib.metadata.version(name) != version for name, version in pins.items()):
        raise ValueError('framework pin mismatch')
    names = {'torch': 'torch', 'transformers': 'transformers', 'tokenizers': 'tokenizers',
             'safetensors': 'safetensors', 'huggingface-hub': 'huggingface_hub', 'numpy': 'numpy'}
    modules = {name: importlib.import_module(module) for name, module in names.items()}
    origins = {name: str(Path(module.__file__).resolve()) for name, module in modules.items()}
    if any(not path.startswith('/packages/') for path in origins.values()):
        raise ValueError('framework origin mismatch')
    torch, transformers = modules['torch'], modules['transformers']
    if torch.__version__ != pins['torch'] or transformers.__version__ != pins['transformers']:
        raise ValueError('framework version mismatch')
    from safetensors.torch import save_file
    from tokenizers import Tokenizer, models, pre_tokenizers, processors

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(20261112)
    config = transformers.XLMRobertaConfig(
        vocab_size=20, hidden_size=1024, num_hidden_layers=1, num_attention_heads=16,
        intermediate_size=32, max_position_embeddings=8194, pad_token_id=1,
        bos_token_id=0, eos_token_id=2, hidden_dropout_prob=0.0,
        attention_probs_dropout_prob=0.0,
    )
    config.architectures = ['XLMRobertaModel']
    model = transformers.XLMRobertaModel(config).to(device='cpu', dtype=torch.float32).eval()
    tokenizer = Tokenizer(models.WordLevel(
        {'[CLS]': 0, '[PAD]': 1, '[SEP]': 2, '[UNK]': 3, 'hello': 4, 'world': 5},
        unk_token='[UNK]',
    ))
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
    tokenizer.post_processor = processors.TemplateProcessing(
        single='[CLS] $A [SEP]', special_tokens=[('[CLS]', 0), ('[SEP]', 2)],
    )
    fixed = {
        'tokenizer_config': ('tokenizer_config.json', {'model_max_length': 8192}),
        'special_tokens_map': ('special_tokens_map.json', {}),
        'modules': ('modules.json', [
            {'idx': 0, 'name': '0', 'path': '', 'type': 'sentence_transformers.models.Transformer'},
            {'idx': 1, 'name': '1', 'path': '1_Pooling',
             'type': 'sentence_transformers.models.Pooling'},
            {'idx': 2, 'name': '2', 'path': '2_Normalize',
             'type': 'sentence_transformers.models.Normalize'},
        ]),
        'pooling': ('1_Pooling/config.json', {'word_embedding_dimension': 1024,
                    'pooling_mode_cls_token': True, 'pooling_mode_mean_tokens': False}),
        'sentence_bert_config': ('sentence_bert_config.json',
                                 {'max_seq_length': 8192, 'do_lower_case': False}),
        'sentence_transformers_config': ('config_sentence_transformers.json',
                                         {'__version__': {'sentence_transformers': '2.2.2'}}),
    }
    # The revision is an explicit synthetic identifier, not an upstream checkpoint revision.
    revision = hashlib.sha256(b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40]
    state = {name: tensor.detach().contiguous() for name, tensor in model.state_dict().items()}
    inventories = {}
    for fmt, weight_name in [('safetensors', 'model.safetensors'),
                             ('pytorch-state-dict', 'pytorch_model.bin')]:
        root = target / fmt
        root.mkdir(mode=0o700)
        write_json(root / 'config.json', config.to_dict())
        tokenizer.save(str(root / 'tokenizer.json'))
        (root / 'tokenizer.json').chmod(0o600)
        for name, value in fixed.values():
            write_json(root / name, value)
        if fmt == 'safetensors':
            save_file(state, str(root / weight_name), metadata={'format': 'pt'})
        else:
            torch.save(state, str(root / weight_name))
        (root / weight_name).chmod(0o600)
        paths = {'config': 'config.json', 'tokenizer': 'tokenizer.json',
                 'weights': weight_name} | {role: entry[0] for role, entry in fixed.items()}
        entries = []
        for role, name in paths.items():
            data = (root / name).read_bytes()
            entries.append({'role': role, 'path': name, 'sha256': hashlib.sha256(data).hexdigest(),
                            'size': len(data)})
        inventories[fmt] = {'schema': 2, 'model_name': 'BAAI/bge-m3',
                            'model_revision': revision, 'checkpoint_format': fmt, 'files': entries}
    ids = torch.tensor([[0, 4, 5, 2], [0, 5, 2, 1]], dtype=torch.long, device='cpu')
    mask = torch.tensor([[1, 1, 1, 1], [1, 1, 1, 0]], dtype=torch.long, device='cpu')
    with torch.no_grad():
        output = model(input_ids=ids, attention_mask=mask, return_dict=True)
        rows = output.last_hidden_state[:, 0, :]
    result = {'kind': 'synthetic-random-toy', 'synthetic_revision': revision,
              'inventories': inventories, 'input_ids': [[0, 4, 5, 2], [0, 5, 2]],
              'reference': rows.tolist(), 'torch': torch.__version__,
              'transformers': transformers.__version__, 'python': sys.version,
              'package_versions': pins, 'package_origins': origins,
              'generation_threads': {'intra_op': torch.get_num_threads(),
                                     'inter_op': torch.get_num_interop_threads()},
              'runtime_executable': sys.executable, 'runtime_prefix': sys.base_prefix}
    wire = json.dumps(result, allow_nan=False, separators=(',', ':')).encode()
    if len(wire) > 65535:
        raise ValueError('result exceeds limit')
    os.write(1, wire + b'\n')


def main():
    if len(sys.argv) != 2 or sys.argv[1] != '/output':
        raise ValueError('fixed operation required')
    generate(Path('/output'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('toy generation failed', file=sys.stderr)
        sys.exit(1)
