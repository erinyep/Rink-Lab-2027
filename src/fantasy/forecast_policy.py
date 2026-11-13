"""Category-specific forecast selection with explicit source lineage."""
import numpy as np


def select_fantasy_projections(frame, date, policy):
    keys=['game_id','player_id']
    if frame.duplicated(keys+['model']).any():raise ValueError('Duplicate forecast identity')
    baseline=policy['baseline'];result=frame[frame.model.eq(baseline)].copy()
    if result.empty:raise ValueError('Missing baseline forecasts')
    selected_policy=None
    for historical in policy.get('policy_history',[]):
        if date>=historical['effective_from'] and date<=historical['effective_through']:
            selected_policy=historical
            break
    if date>=policy['effective_from']:
        selected_policy=policy
    if selected_policy is None:return result
    result=result.set_index(keys)
    for category,source in selected_policy['category_models'].items():
        column='expected_'+category+'_if_plays'
        selected=frame[frame.model.eq(source)].set_index(keys)
        if set(selected.index)!=set(result.index):raise ValueError('Category policy coverage mismatch')
        values=selected[column].reindex(result.index)
        if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid selected conditional mean')
        result['baseline_'+column]=result[column]
        result[column]=values
        result[category+'_source_model']=source
    result['model']=selected_policy['version']
    return result.reset_index()
