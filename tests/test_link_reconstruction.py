from orphan_radar.core.models import NoteRecord
from orphan_radar.eval.link_reconstruction import mask_hidden_link_text


def test_link_reconstruction_masks_hidden_link_text():
    note = NoteRecord(
        note_id='a', filepath='a.md', relpath='a.md', title='A',
        content='See [[Target Note]] and Target Note again.', search_text='', file_hash='x', folder_path=''
    )
    masked = mask_hidden_link_text(note, 'Target Note')
    assert '[[Target Note]]' not in masked.content
    assert 'Target Note again' not in masked.content
