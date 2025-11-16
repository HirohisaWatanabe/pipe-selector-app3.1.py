import streamlit as st
import math

# --- 1. データの定義 ---
# 実際の値はメーカーカタログ等で確認し、正確な値に置き換えてください。
# 例: '種類': 外径を元に計算された断面積(mm^2)
CABLE_AREAS = {
    'CVT22sq': 452.16,
    'CVT38sq': 615.44,
    'CVT60sq': 854.87,
    'CVT100sq': 1319.59,
    'CVT150sq': 1734.07,
    'CVT200sq': 2374.63,
    'CVT250sq': 2826,

    'IV5.5sq': 19.63,
    'IV8sq': 28.26,
    'IV14sq': 45.34,
    'IV22sq': 66.44,
    'IV38sq': 103.82,
    'IV60sq': 153.86,
    'IV100sq': 226.87,

    'FCPEV0.9mmx2P': 35.24,
    'FCPEV1.2mmx2P': 51.5,
    'CVV-S2sq-3C': 94.99,
    'CVV-S2sq-4C': 103.82,
    'CVV3.5sq-3C': 113.0,
    'CVV5.5sq-3C': 165.0,
    'PV4.0sq': 34.19,
    'PV5.5sq': 38.47,
}

# 例: '種類_呼び径': 内側断面積(mm^2)
CONDUIT_AREAS = {
    'G管_16': 201,        # 内径：16.4mm
    'G管_22': 380,        # 内径：21.9mm
    'G管_28': 607,        # 内径：28.3mm
    'G管_36': 1068.86,    # 内径：36.9mm
    'G管_42': 1437.99,    # 内径：42.8mm
    'G管_54': 2289.09,    # 内径：54.0mm
    'G管_70': 3802.66,    # 内径：69.6mm
    'G管_82': 5317.03,    # 内径：82.3mm
    'G管_92': 6892.05,    # 内径：93.7mm

    'PFD管_16': 185,      # 内径：16mm
    'PFD管_22': 320,      # 内径：22mm
    'PFD管_28': 500,      # 内径：28mm
    'PFD管_30': 706.5,    # 内径：30mm
    'PFD管_36': 1017.36,  # 内径：36mm
    'PFD管_42': 1256,     # 内径：40mm

    '防水プリカ_24': 444.65,    # 内径：23.8mm
    '防水プリカ_30': 673.91,    # 内径：29.3mm
    '防水プリカ_38': 1080.48,   # 内径：37.1mm
    '防水プリカ_50': 1892.48,   # 内径：49.1mm
    '防水プリカ_63': 3076.22,   # 内径：62.6mm
    '防水プリカ_76': 4534.16,   # 内径：76.0mm
    '防水プリカ_83': 5150.38,   # 内径：81.0mm

    'FEP管_30': 706.5,     # 内径：30.0mm
    'FEP管_40': 1384.74,   # 内径：42.0mm
    'FEP管_50': 1962.5,    # 内径：50.0mm
    'FEP管_65': 3419.46,   # 内径：66.0mm
    'FEP管_80': 5024,      # 内径：80.0mm
    'FEP管_100': 7850,     # 内径：100.0mm
    'FEP管_125': 12265.62, # 内径：125.0mm

}

# 占有率の上限 (48%)
FILL_FACTOR_LIMIT = 0.48 

# --- 2. 処理ロジックの定義 ---
def select_conduit_size(total_cable_area, conduit_type):
    """
    ケーブルの総断面積と配管の種類に基づいて、占有率48%以下で
    最小の配管サイズを選定します。
    """
    if total_cable_area <= 0:
        return (False, "エラー: ケーブルの総断面積がゼロまたは負の値です。")

    # 必要な配管の最小断面積を計算 (mm^2)
    required_conduit_area = total_cable_area / FILL_FACTOR_LIMIT

    # 該当する配管の種類で、必要な断面積を満たす最小のサイズを選定
    matching_conduits = {k: v for k, v in CONDUIT_AREAS.items() if k.startswith(conduit_type)}
    
    if not matching_conduits:
        return (False, f"エラー: 配管 '{conduit_type}' のデータが見つかりません。")

    selected_size = None
    min_sufficient_area = float('inf')

    # 最小の適切なサイズを探索
    for name, area in matching_conduits.items():
        if area >= required_conduit_area:
            if area < min_sufficient_area:
                min_sufficient_area = area
                selected_size = name
    
    if selected_size:
        # 選定された配管での実際の占有率を計算
        actual_fill_factor = total_cable_area / min_sufficient_area
        
        # 結果メッセージ
        message = (
            f"✅ 選定された配管: **{selected_size}**\n"
            f"- 配管断面積: {min_sufficient_area:.2f} mm²\n"
            f"- ケーブル総断面積: {total_cable_area:.2f} mm²\n"
            f"- **実際の占有率**: **{actual_fill_factor*100:.1f} %** (基準: 48.0 %)"
        )
        return (True, message)
    else:
        max_area_in_type = max(matching_conduits.values())
        return (False, f"❌ エラー: {conduit_type} の最大サイズ "
                       f"({max_area_in_type:.2f} mm²) でも断面積が不足しています。より大きな配管が必要です。")

# --- 3. Streamlit UIと状態管理 ---
st.title('🔩 配管太さ選定アプリ (複数ケーブル対応・占有率48%)')
st.markdown('複数のケーブルの組み合わせと配管の種類に基づき、最小の配管サイズを選定します。')
st.markdown('**注意**: 占有率48%は、3本以上の電線を収める場合の基準値です。')

# セッションステートの初期化
if 'cables' not in st.session_state:
    st.session_state.cables = []

cable_options = list(CABLE_AREAS.keys())
conduit_options = sorted(list(set([k.split('_')[0] for k in CONDUIT_AREAS.keys()])))

# ケーブル追加関数
def add_cable():
    cable_type = st.session_state.new_cable_type
    cable_count = st.session_state.new_cable_count
    
    # 入力値の検証
    if cable_count < 1:
        st.warning('本数は1以上である必要があります。')
        return

    cable_area = CABLE_AREAS[cable_type]
    
    st.session_state.cables.append({
        'type': cable_type,
        'count': cable_count,
        'area': cable_area
    })
    # 入力フィールドをリセット（Streamlitの仕様上、再描画で自動リセットされるため不要なことが多いが、明示的にクリアする場合は使う）
    # st.session_state.new_cable_type = cable_options[0]
    # st.session_state.new_cable_count = 1

# ケーブル削除関数
def remove_cable(index):
    st.session_state.cables.pop(index)

# --- ステップ 1: ケーブルの追加 ---
st.header('ステップ 1: ケーブルの追加')

with st.form('add_cable_form', clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.selectbox(
            '線種を選択',
            cable_options,
            key='new_cable_type'
        )
    with col2:
        st.number_input(
            '本数',
            min_value=1,
            value=3,
            step=1,
            key='new_cable_count'
        )
        
    st.form_submit_button('➕ ケーブルを追加', on_click=add_cable)

# --- ステップ 2: 選択されたケーブルの確認 ---
st.header('ステップ 2: 選択されたケーブルの確認')

if st.session_state.cables:
    
    # DataFrame形式で表示（見やすくするため）
    data = []
    total_area_sum = 0
    for cable in st.session_state.cables:
        total_cable_area = cable['area'] * cable['count']
        total_area_sum += total_cable_area
        data.append({
            '線種': cable['type'],
            '本数': cable['count'],
            '単体断面積 (mm²)': f"{cable['area']:.2f}",
            '合計断面積 (mm²)': f"{total_cable_area:.2f}"
        })

    st.dataframe(data, hide_index=True, use_container_width=True)
    st.success(f"**総断面積**: **{total_area_sum:.2f} mm²**")

    # 削除ボタンの配置 (ループで動的に生成)
    st.markdown("---")
    st.caption("個別削除:")
    cols = st.columns(len(st.session_state.cables))
    for i, cable in enumerate(st.session_state.cables):
        cols[i].button(
            f"❌ {cable['type']} ({cable['count']}本)", 
            key=f"remove_{i}", 
            on_click=remove_cable, 
            args=(i,)
        )
        
else:
    st.info('ケーブルが追加されていません。上記フォームから追加してください。')
    total_area_sum = 0

# --- ステップ 3: 配管の選定 ---
st.header('ステップ 3: 配管の選定')

if st.session_state.cables:
    
    # 配管の種類の選択
    selected_conduit = st.selectbox(
        '管種を選択:',
        conduit_options,
        key='selected_conduit_type'
    )

    if st.button('🚀 配管サイズを選定する'):
        # 計算実行
        success, result_message = select_conduit_size(
            total_area_sum, 
            selected_conduit
        )
        
        # 結果表示
        if success:
            st.success('選定完了！')
            st.code(result_message)
            
            # 詳細情報の表示
            required_area = total_area_sum / FILL_FACTOR_LIMIT
            st.info(f"""
            **選定基準:**
            - ケーブル総断面積: {total_area_sum:.2f} mm²
            - 占有率の上限: {FILL_FACTOR_LIMIT*100:.0f} %
            - 必要な最小配管断面積: {required_area:.2f} mm²
            """)

        else:
            st.error(result_message)
            
else:
    st.warning('ケーブルが追加されていません。ステップ1でケーブルを追加してから実行してください。')