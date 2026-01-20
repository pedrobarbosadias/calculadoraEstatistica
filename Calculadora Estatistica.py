import streamlit as st
import numpy as np
from scipy import stats
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configurar página
st.set_page_config(
    page_title="Calculadora A/B Testing",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ff6b6b;
}
.success-card {
    background-color: #d4edda;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
}
.warning-card {
    background-color: #fff3cd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ffc107;
}
.error-card {
    background-color: #f8d7da;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("🎯 Calculadora Completa de Testes A/B")
st.markdown("**Planeje, execute e valide seus testes A/B com precisão estatística**")

# === FUNÇÕES BACKEND (suas funções originais) ===
def calcular_tamanho_amostra_ab(taxa_base, melhoria_minima_detectar, poder_estatistico=0.80, nivel_significancia=0.05, split_ratio=0.5):
    # Determinar se é melhoria absoluta ou relativa
    if melhoria_minima_detectar > taxa_base:
        taxa_variacao = taxa_base * (1 + melhoria_minima_detectar)
        effect_size = taxa_variacao - taxa_base
        tipo_melhoria = "relativa"
    else:
        effect_size = melhoria_minima_detectar
        taxa_variacao = taxa_base + effect_size
        tipo_melhoria = "absoluta"
    
    # Z-scores
    z_alpha = stats.norm.ppf(1 - nivel_significancia/2)
    z_beta = stats.norm.ppf(poder_estatistico)
    
    # Proporção média
    p_avg = (taxa_base + taxa_variacao) / 2
    
    # Cálculo do tamanho da amostra por grupo
    numerator = (z_alpha + z_beta) ** 2 * p_avg * (1 - p_avg)
    denominator = effect_size ** 2
    n_per_group = numerator / denominator
    
    # Ajustar para split ratio
    n_control = int(np.ceil(n_per_group / split_ratio))
    n_treatment = int(np.ceil(n_per_group / (1 - split_ratio)))
    n_total = n_control + n_treatment
    
    # Calcular métricas derivadas
    melhoria_relativa = (effect_size / taxa_base) * 100
    
    return {
        'n_controle': n_control,
        'n_variacao': n_treatment, 
        'n_total': n_total,
        'taxa_base': taxa_base,
        'taxa_variacao': taxa_variacao,
        'effect_size': effect_size,
        'melhoria_relativa': melhoria_relativa,
        'poder_estatistico': poder_estatistico,
        'nivel_significancia': nivel_significancia,
        'tipo_melhoria': tipo_melhoria
    }

def calcular_teste_atual(conversions_a, visitors_a, conversions_b, visitors_b):
    """Calcula métricas do teste atual"""
    p_a = conversions_a / visitors_a
    p_b = conversions_b / visitors_b
    diff_abs = p_b - p_a
    diff_rel = (p_b - p_a) / p_a * 100 if p_a > 0 else 0
    
    # Teste estatístico
    p_pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    se_diff = np.sqrt(p_pooled * (1 - p_pooled) * (1/visitors_a + 1/visitors_b))
    z_score = diff_abs / se_diff if se_diff > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score))) if z_score != 0 else 1
    
    # IC 95%
    margin = 1.96 * se_diff
    ci_lower = diff_abs - margin
    ci_upper = diff_abs + margin
    
    return {
        'p_a': p_a, 'p_b': p_b, 'diff_abs': diff_abs, 'diff_rel': diff_rel,
        'z_score': z_score, 'p_value': p_value, 'ci_lower': ci_lower, 'ci_upper': ci_upper
    }

# === SIDEBAR PARA NAVEGAÇÃO ===
st.sidebar.title("🔧 Navegação")
opcao = st.sidebar.selectbox(
    "Escolha a funcionalidade:",
    ["🎯 Planejar Novo Teste", "🔍 Validar Teste em Andamento", "⚡ Cálculo Rápido", "📊 Análise Completa"]
)

# === ABA 1: PLANEJAR NOVO TESTE ===
if opcao == "🎯 Planejar Novo Teste":
    st.header("🎯 Planejamento de Novo Teste A/B")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Dados Básicos")
        taxa_base = st.number_input(
            "Taxa de Conversão Atual (%)", 
            min_value=0.1, max_value=100.0, value=5.0, step=0.1,
            help="Sua taxa de conversão atual em percentual"
        ) / 100
        
        tipo_melhoria = st.radio(
            "Tipo de Melhoria Esperada:",
            ["Relativa (%)", "Absoluta (pontos percentuais)"]
        )
        
        if tipo_melhoria == "Relativa (%)":
            melhoria = st.number_input(
                "Melhoria Esperada (%)", 
                min_value=1.0, max_value=100.0, value=20.0, step=1.0,
                help="Ex: 20% significa que espera melhorar em 20% a taxa atual"
            ) / 100
        else:
            melhoria = st.number_input(
                "Melhoria Esperada (pontos percentuais)", 
                min_value=0.1, max_value=10.0, value=1.0, step=0.1,
                help="Ex: 1.0 significa esperar ir de 5% para 6%"
            ) / 100
        
        trafego_diario = st.number_input(
            "Tráfego Diário (visitantes/dia)", 
            min_value=100, max_value=100000, value=1000, step=100
        )
        
        orcamento_dias = st.number_input(
            "Orçamento Máximo (dias)", 
            min_value=7, max_value=365, value=30, step=1
        )
    
    with col2:
        st.subheader("⚙️ Configurações Avançadas")
        poder_estatistico = st.select_slider(
            "Poder Estatístico",
            options=[0.70, 0.80, 0.85, 0.90, 0.95],
            value=0.80,
            help="Probabilidade de detectar o efeito se ele existir"
        )
        
        nivel_significancia = st.select_slider(
            "Nível de Significância",
            options=[0.01, 0.05, 0.10],
            value=0.05,
            help="Probabilidade de falso positivo"
        )
        
        split_ratio = st.slider(
            "Proporção de Tráfego (Controle/Variação)",
            min_value=0.3, max_value=0.7, value=0.5, step=0.1,
            help="0.5 = 50%/50%, 0.6 = 60%/40%"
        )
        
        nome_teste = st.text_input(
            "Nome do Teste",
            value="Meu Teste A/B",
            help="Para identificação nos resultados"
        )
    
    if st.button("📊 Calcular Tamanho da Amostra", type="primary"):
        resultado = calcular_tamanho_amostra_ab(
            taxa_base=taxa_base,
            melhoria_minima_detectar=melhoria,
            poder_estatistico=poder_estatistico,
            nivel_significancia=nivel_significancia,
            split_ratio=split_ratio
        )
        
        # Cálculos de viabilidade
        dias_necessarios = resultado['n_total'] // trafego_diario
        viavel = dias_necessarios <= orcamento_dias
        
        # Resultados principais
        st.markdown("---")
        st.subheader(f"📋 Resultados para: {nome_teste}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Visitantes", f"{resultado['n_total']:,}")
        with col2:
            st.metric("Grupo Controle", f"{resultado['n_controle']:,}")
        with col3:
            st.metric("Grupo Variação", f"{resultado['n_variacao']:,}")
        with col4:
            st.metric("Duração Estimada", f"{dias_necessarios} dias")
        
        # Status de viabilidade
        if viavel:
            st.markdown("""
            <div class="success-card">
                <h4>✅ TESTE VIÁVEL</h4>
                <p>O teste pode ser executado dentro do orçamento de tempo!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-card">
                <h4>❌ TESTE INVIÁVEL</h4>
                <p>Precisa de {dias_necessarios} dias, mas o orçamento é de {orcamento_dias} dias.</p>
                <p><strong>Sugestões:</strong></p>
                <ul>
                    <li>Aumentar orçamento para {dias_necessarios} dias</li>
                    <li>Testar melhoria maior ({melhoria*1.5*100:.1f}%)</li>
                    <li>Reduzir poder estatístico para 70%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de cenários
        st.subheader("📊 Análise de Cenários")
        
        # Criar cenários alternativos
        melhorias_cenario = [melhoria*0.5, melhoria, melhoria*1.5, melhoria*2]
        nomes_cenario = ["Conservador", "Esperado", "Otimista", "Agressivo"]
        
        dados_cenarios = []
        for i, mel in enumerate(melhorias_cenario):
            if taxa_base + mel <= 1.0:
                res_temp = calcular_tamanho_amostra_ab(
                    taxa_base=taxa_base,
                    melhoria_minima_detectar=mel,
                    poder_estatistico=poder_estatistico,
                    nivel_significancia=nivel_significancia,
                    split_ratio=split_ratio
                )
                dias_temp = res_temp['n_total'] // trafego_diario
                
                dados_cenarios.append({
                    'Cenário': nomes_cenario[i],
                    'Melhoria (%)': f"{res_temp['melhoria_relativa']:.1f}%",
                    'Amostra Total': res_temp['n_total'],
                    'Dias Necessários': dias_temp,
                    'Viável': "✅ Sim" if dias_temp <= orcamento_dias else "❌ Não"
                })
        
        df_cenarios = pd.DataFrame(dados_cenarios)
        st.dataframe(df_cenarios, use_container_width=True)
        
        # Gráfico de barras
        fig = px.bar(
            dados_cenarios, 
            x='Cenário', 
            y='Dias Necessários',
            color='Dias Necessários',
            title="Duração do Teste por Cenário"
        )
        fig.add_hline(y=orcamento_dias, line_dash="dash", line_color="red", 
                     annotation_text=f"Orçamento: {orcamento_dias} dias")
        st.plotly_chart(fig, use_container_width=True)

# === ABA 2: VALIDAR TESTE EM ANDAMENTO ===
elif opcao == "🔍 Validar Teste em Andamento":
    st.header("🔍 Validação de Teste em Andamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Dados do Grupo A (Controle)")
        conversions_a = st.number_input("Conversões Grupo A", min_value=0, value=516)
        visitors_a = st.number_input("Visitantes Grupo A", min_value=1, value=7465)
        taxa_a = conversions_a / visitors_a if visitors_a > 0 else 0
        st.write(f"Taxa de Conversão A: **{taxa_a:.2%}**")
    
    with col2:
        st.subheader("📊 Dados do Grupo B (Variação)")  
        conversions_b = st.number_input("Conversões Grupo B", min_value=0, value=453)
        visitors_b = st.number_input("Visitantes Grupo B", min_value=1, value=6557)
        taxa_b = conversions_b / visitors_b if visitors_b > 0 else 0
        st.write(f"Taxa de Conversão B: **{taxa_b:.2%}**")
    
    st.subheader("🎯 Configurações de Validação")
    col3, col4 = st.columns(2)
    
    with col3:
        melhoria_esperada = st.number_input(
            "Melhoria Mínima Esperada (%)", 
            min_value=1.0, max_value=100.0, value=10.0, step=1.0
        ) / 100
    
    with col4:
        poder_validacao = st.select_slider(
            "Poder Estatístico",
            options=[0.70, 0.80, 0.85, 0.90],
            value=0.80
        )
    
    if st.button("🔍 Analisar Teste Atual", type="primary"):
        # Calcular métricas do teste atual
        resultado_atual = calcular_teste_atual(conversions_a, visitors_a, conversions_b, visitors_b)
        
        # Calcular amostra ideal
        resultado_ideal = calcular_tamanho_amostra_ab(
            taxa_base=resultado_atual['p_a'],
            melhoria_minima_detectar=melhoria_esperada,
            poder_estatistico=poder_validacao
        )
        
        amostra_atual = visitors_a + visitors_b
        percentual_coletado = (amostra_atual / resultado_ideal['n_total']) * 100
        
        st.markdown("---")
        st.subheader("📈 Resultados da Análise")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Diferença Absoluta", f"{resultado_atual['diff_abs']:+.2%}")
        with col2:
            st.metric("Diferença Relativa", f"{resultado_atual['diff_rel']:+.1f}%")
        with col3:
            st.metric("P-valor", f"{resultado_atual['p_value']:.4f}")
        with col4:
            significativo = "✅ Sim" if resultado_atual['p_value'] < 0.05 else "❌ Não"
            st.metric("Significativo", significativo)
        
        # Status do teste
        if resultado_atual['p_value'] < 0.05:
            st.markdown("""
            <div class="success-card">
                <h4>✅ TESTE SIGNIFICATIVO</h4>
                <p>Há evidência estatística de diferença entre os grupos!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            if percentual_coletado >= 100:
                st.markdown("""
                <div class="warning-card">
                    <h4>⚠️ TESTE COMPLETO MAS NÃO SIGNIFICATIVO</h4>
                    <p>Você coletou dados suficientes, mas não detectou diferença significativa.</p>
                    <p>Isso pode significar que não há diferença real entre as variações.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                falta = resultado_ideal['n_total'] - amostra_atual
                st.markdown(f"""
                <div class="warning-card">
                    <h4>🟡 TESTE EM ANDAMENTO</h4>
                    <p>Progresso: {percentual_coletado:.1f}% da amostra ideal</p>
                    <p>Faltam aproximadamente: <strong>{falta:,} visitantes</strong></p>
                    <p>Amostra atual: {amostra_atual:,} | Amostra ideal: {resultado_ideal['n_total']:,}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Intervalo de confiança
        st.subheader("📊 Intervalo de Confiança 95%")
        ic_texto = f"[{resultado_atual['ci_lower']:.3%}, {resultado_atual['ci_upper']:.3%}]"
        
        if 0 >= resultado_atual['ci_lower'] and 0 <= resultado_atual['ci_upper']:
            st.error(f"IC contém zero: {ic_texto} - Não significativo")
        else:
            st.success(f"IC não contém zero: {ic_texto} - Significativo")
        
        # Gráfico do intervalo de confiança
        fig_ic = go.Figure()
        
        # Linha do intervalo
        fig_ic.add_trace(go.Scatter(
            x=[resultado_atual['ci_lower']*100, resultado_atual['ci_upper']*100], 
            y=[1, 1],
            mode='lines+markers',
            line=dict(width=8, color='blue'),
            marker=dict(size=10),
            name='IC 95%'
        ))
        
        # Ponto da diferença observada
        fig_ic.add_trace(go.Scatter(
            x=[resultado_atual['diff_abs']*100], 
            y=[1],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Diferença Observada'
        ))
        
        # Linha do zero
        fig_ic.add_vline(x=0, line_dash="dash", line_color="gray", 
                        annotation_text="Diferença = 0")
        
        fig_ic.update_layout(
            title="Intervalo de Confiança da Diferença",
            xaxis_title="Diferença (%)",
            yaxis=dict(showticklabels=False, range=[0.5, 1.5]),
            height=300
        )
        
        st.plotly_chart(fig_ic, use_container_width=True)

# === ABA 3: CÁLCULO RÁPIDO ===
elif opcao == "⚡ Cálculo Rápido":
    st.header("⚡ Cálculo Rápido de Amostra")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        taxa_base_rapida = st.number_input(
            "Taxa de Conversão Atual (%)", 
            min_value=0.1, max_value=100.0, value=7.0, step=0.1
        ) / 100
    
    with col2:
        melhoria_rapida = st.number_input(
            "Melhoria Esperada (%)", 
            min_value=1.0, max_value=200.0, value=25.0, step=1.0
        )
    
    with col3:
        trafego_rapido = st.number_input(
            "Tráfego Diário", 
            min_value=100, max_value=50000, value=1000, step=100
        )
    
    if st.button("⚡ Calcular Rapidamente"):
        melhoria_absoluta = taxa_base_rapida * (melhoria_rapida / 100)
        
        resultado_rapido = calcular_tamanho_amostra_ab(
            taxa_base=taxa_base_rapida,
            melhoria_minima_detectar=melhoria_absoluta
        )
        
        dias_rapido = resultado_rapido['n_total'] // trafego_rapido
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Visitantes Necessários", f"{resultado_rapido['n_total']:,}")
        with col2:
            st.metric("Duração Estimada", f"{dias_rapido} dias")
        with col3:
            conversoes_esperadas = int(resultado_rapido['n_variacao'] * resultado_rapido['taxa_variacao'])
            st.metric("Conversões Esperadas (B)", f"{conversoes_esperadas}")

# === ABA 4: ANÁLISE COMPLETA ===
elif opcao == "📊 Análise Completa":
    st.header("📊 Análise Completa de Teste A/B")
    
    # Upload de dados ou entrada manual
    opcao_dados = st.radio(
        "Como você quer inserir os dados?",
        ["✍️ Entrada Manual", "📁 Upload de Arquivo CSV"]
    )
    
    if opcao_dados == "✍️ Entrada Manual":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Grupo A (Controle)")
            conv_a = st.number_input("Conversões A", min_value=0, value=245, key="conv_a")
            visit_a = st.number_input("Visitantes A", min_value=1, value=5000, key="visit_a")
        
        with col2:
            st.subheader("Grupo B (Variação)")
            conv_b = st.number_input("Conversões B", min_value=0, value=312, key="conv_b")  
            visit_b = st.number_input("Visitantes B", min_value=1, value=5200, key="visit_b")
        
        dados = {
            'conversions_a': conv_a, 'visitors_a': visit_a,
            'conversions_b': conv_b, 'visitors_b': visit_b
        }
        
    else:
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df.head())
            
            # Assumindo colunas específicas
            if all(col in df.columns for col in ['conversions_a', 'visitors_a', 'conversions_b', 'visitors_b']):
                dados = {
                    'conversions_a': df['conversions_a'].iloc[0],
                    'visitors_a': df['visitors_a'].iloc[0],
                    'conversions_b': df['conversions_b'].iloc[0],
                    'visitors_b': df['visitors_b'].iloc[0]
                }
            else:
                st.error("O arquivo deve conter as colunas: conversions_a, visitors_a, conversions_b, visitors_b")
                dados = None
        else:
            dados = None
    
    if dados and st.button("📊 Análise Completa", type="primary"):
        resultado_completo = calcular_teste_atual(
            dados['conversions_a'], dados['visitors_a'],
            dados['conversions_b'], dados['visitors_b']
        )
        
        # Dashboard de métricas
        st.markdown("---")
        st.subheader("📈 Dashboard de Resultados")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Taxa A", f"{resultado_completo['p_a']:.2%}")
        with col2:
            st.metric("Taxa B", f"{resultado_completo['p_b']:.2%}")
        with col3:
            st.metric("Diferença", f"{resultado_completo['diff_abs']:+.2%}")
        with col4:
            st.metric("Melhoria", f"{resultado_completo['diff_rel']:+.1f}%")
        with col5:
            st.metric("P-valor", f"{resultado_completo['p_value']:.4f}")
        
        # Gráfico de comparação
        fig_compare = go.Figure(data=[
            go.Bar(name='Grupo A', x=['Taxa de Conversão'], y=[resultado_completo['p_a']*100]),
            go.Bar(name='Grupo B', x=['Taxa de Conversão'], y=[resultado_completo['p_b']*100])
        ])
        
        fig_compare.update_layout(
            title="Comparação de Taxa de Conversão",
            yaxis_title="Taxa de Conversão (%)",
            barmode='group'
        )
        
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # Conclusão final
        if resultado_completo['p_value'] < 0.05:
            if resultado_completo['diff_abs'] > 0:
                st.success("🎉 **GRUPO B É SIGNIFICATIVAMENTE MELHOR!** Implemente a variação.")
            else:
                st.error("📉 **GRUPO A É SIGNIFICATIVAMENTE MELHOR!** Mantenha o controle.")
        else:
            st.warning("🤷 **SEM DIFERENÇA SIGNIFICATIVA** - Não há evidência de diferença real entre os grupos.")

# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>📊 <strong>Calculadora A/B Testing</strong> | Desenvolvido para otimizar seus testes</p>
    <p><small>Baseado em métodos estatísticos rigorosos e melhores práticas de experimentação</small></p>
</div>
""", unsafe_allow_html=True)