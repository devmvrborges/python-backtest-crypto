from binance.client import Client
import datetime, pandas as pd
import numpy as np

client = Client()
start = datetime.datetime(2024, 6, 30)
end = datetime.datetime(2025, 6, 30)

klines = client.get_historical_klines(
    'BTCBRL',  # Bitcoin em Reais
    Client.KLINE_INTERVAL_4HOUR,  # Intervalos de 4 horas
    str(start),
    str(end)
)

df = pd.DataFrame(
    klines,
    columns=['Hora Abertura', 'Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume', 'Hora Fechamento',
             'Volume Ativo Quote','Número de Trades','Volume Base Compra Taker',
             'Volume Quote Compra Taker','Ignorar']
)
df['Hora Abertura'] = pd.to_datetime(df['Hora Abertura'], unit='ms')

# Converter preços para float
df['Fechamento'] = df['Fechamento'].astype(float)
df['Abertura'] = df['Abertura'].astype(float)
df['Máxima'] = df['Máxima'].astype(float)
df['Mínima'] = df['Mínima'].astype(float)

# Função para calcular EMA
def calcular_ema(precos, periodo):
    return precos.ewm(span=periodo, adjust=False).mean()

# Função para calcular RSI
def calcular_rsi(precos, periodo=14):
    delta = precos.diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganho / perda
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Calcular indicadores técnicos
df['EMA_9'] = calcular_ema(df['Fechamento'], 9)
df['EMA_21'] = calcular_ema(df['Fechamento'], 21)
df['RSI'] = calcular_rsi(df['Fechamento'], 14)

# Estratégia EMA 9/21 + RSI
valor_operacao = 100.00  # R$ 100,00 por operação
taxa_transacao = 0.001  # 0,10% de taxa por transação
rsi_oversold = 30  # RSI abaixo de 30 = sobrevendido
rsi_overbought = 70  # RSI acima de 70 = sobrecomprado

# Variáveis de controle
saldo_reais = 0.0
bitcoin_acumulado = 0.0
total_investido = 0.0
total_vendido = 0.0
total_taxas = 0.0
posicao_aberta = False
preco_compra = 0.0

historico_operacoes = []
print("=== SIMULAÇÃO DE ESTRATÉGIA EMA 9/21 + RSI EM BITCOIN ===")
print(f"Estratégia: EMA 9/21 crossover + RSI (sobrevendido < {rsi_oversold}, sobrecomprado > {rsi_overbought})")
print(f"Timeframe: 4 horas")
print(f"Valor por operação: R$ {valor_operacao:.2f}")
print(f"Taxa por transação: {taxa_transacao*100:.2f}%")
print(f"Período: {start.strftime('%d/%m/%Y')} até {end.strftime('%d/%m/%Y')}")
print("\n" + "="*80)

# Simular operações baseadas na estratégia EMA + RSI
for index, row in df.iterrows():
    # Pular primeiras linhas até termos dados suficientes para os indicadores
    if index < 21:  # Precisamos de pelo menos 21 períodos para EMA_21
        continue
        
    preco_atual = row['Fechamento']
    data_operacao = row['Hora Abertura']
    ema_9 = row['EMA_9']
    ema_21 = row['EMA_21']
    rsi = row['RSI']
    
    # Verificar se temos dados válidos
    if pd.isna(ema_9) or pd.isna(ema_21) or pd.isna(rsi):
        continue
    
    # Condições para COMPRA:
    # 1. EMA 9 cruza acima da EMA 21 (tendência de alta)
    # 2. RSI está em território de sobrevendido (< 30) ou neutro (30-50)
    if not posicao_aberta and index > 0:
        ema_9_anterior = df['EMA_9'].iloc[index-1]
        ema_21_anterior = df['EMA_21'].iloc[index-1]
        
        # Crossover: EMA 9 cruza acima da EMA 21
        crossover_alta = (ema_9_anterior <= ema_21_anterior) and (ema_9 > ema_21)
        
        # RSI favorável para compra
        rsi_favoravel_compra = rsi < 50  # RSI não está em território de sobrecompra
        
        if crossover_alta and rsi_favoravel_compra:
            # COMPRAR Bitcoin
            taxa_compra = valor_operacao * taxa_transacao
            valor_liquido = valor_operacao - taxa_compra
            bitcoin_comprado = valor_liquido / preco_atual
            
            bitcoin_acumulado += bitcoin_comprado
            total_investido += valor_operacao
            total_taxas += taxa_compra
            preco_compra = preco_atual
            posicao_aberta = True
            
            historico_operacoes.append({
                'Data': data_operacao,
                'Tipo': 'COMPRA',
                'Preço BTC (R$)': preco_atual,
                'Valor Operação (R$)': valor_operacao,
                'Taxa (R$)': taxa_compra,
                'BTC Comprado/Vendido': bitcoin_comprado,
                'BTC Total': bitcoin_acumulado,
                'EMA_9': ema_9,
                'EMA_21': ema_21,
                'RSI': rsi,
                'Sinal': 'EMA Crossover + RSI Favorável',
                'Total Investido (R$)': total_investido,
                'Total Vendido (R$)': total_vendido
            })
    
    # Condições para VENDA:
    # 1. EMA 9 cruza abaixo da EMA 21 (tendência de baixa) OU
    # 2. RSI está em território de sobrecomprado (> 70)
    elif posicao_aberta and index > 0:
        ema_9_anterior = df['EMA_9'].iloc[index-1]
        ema_21_anterior = df['EMA_21'].iloc[index-1]
        
        # Crossover: EMA 9 cruza abaixo da EMA 21
        crossover_baixa = (ema_9_anterior >= ema_21_anterior) and (ema_9 < ema_21)
        
        # RSI em território de sobrecompra
        rsi_sobrecomprado = rsi > rsi_overbought
        
        if crossover_baixa or rsi_sobrecomprado:
            # VENDER Bitcoin
            valor_venda_bruto = bitcoin_acumulado * preco_atual
            taxa_venda = valor_venda_bruto * taxa_transacao
            valor_venda_liquido = valor_venda_bruto - taxa_venda
            
            saldo_reais += valor_venda_liquido
            total_vendido += valor_venda_liquido
            total_taxas += taxa_venda
            bitcoin_vendido = bitcoin_acumulado
            bitcoin_acumulado = 0.0
            posicao_aberta = False
            
            sinal_venda = 'EMA Crossover Baixa' if crossover_baixa else 'RSI Sobrecomprado'
            
            historico_operacoes.append({
                'Data': data_operacao,
                'Tipo': 'VENDA',
                'Preço BTC (R$)': preco_atual,
                'Valor Operação (R$)': valor_venda_liquido,
                'Taxa (R$)': taxa_venda,
                'BTC Comprado/Vendido': -bitcoin_vendido,
                'BTC Total': bitcoin_acumulado,
                'EMA_9': ema_9,
                'EMA_21': ema_21,
                'RSI': rsi,
                'Sinal': sinal_venda,
                'Total Investido (R$)': total_investido,
                'Total Vendido (R$)': total_vendido
            })

# Calcular resultado final
preco_final = df['Fechamento'].iloc[-1]
valor_bitcoin_restante = bitcoin_acumulado * preco_final
patrimonio_total = saldo_reais + valor_bitcoin_restante
lucro_prejuizo = patrimonio_total - total_investido

if total_investido > 0:
    rentabilidade_percentual = (lucro_prejuizo / total_investido) * 100
else:
    rentabilidade_percentual = 0

# Exibir resultados
print(f"\n=== RESULTADOS FINAIS ===")
print(f"Total de operações realizadas: {len(historico_operacoes)}")
operacoes_compra = len([op for op in historico_operacoes if op['Tipo'] == 'COMPRA'])
operacoes_venda = len([op for op in historico_operacoes if op['Tipo'] == 'VENDA'])
print(f"Operações de compra: {operacoes_compra}")
print(f"Operações de venda: {operacoes_venda}")
print(f"Total investido: R$ {total_investido:.2f}")
print(f"Total vendido: R$ {total_vendido:.2f}")
print(f"Saldo em reais: R$ {saldo_reais:.2f}")
print(f"Bitcoin restante: {bitcoin_acumulado:.8f} BTC")
print(f"Valor do Bitcoin restante: R$ {valor_bitcoin_restante:.2f}")
print(f"Patrimônio total: R$ {patrimonio_total:.2f}")
print(f"Total gasto em taxas: R$ {total_taxas:.2f}")
print(f"Lucro/Prejuízo: R$ {lucro_prejuizo:.2f}")
print(f"Rentabilidade: {rentabilidade_percentual:.2f}%")

# Criar DataFrame com histórico de operações
if historico_operacoes:
    df_historico = pd.DataFrame(historico_operacoes)
    
    # Mostrar primeiras e últimas operações
    print(f"\n=== PRIMEIRAS 5 OPERAÇÕES ===")
    print(df_historico[['Data', 'Tipo', 'Preço BTC (R$)', 'RSI', 'Sinal', 'BTC Total']].head().to_string(index=False))
    
    print(f"\n=== ÚLTIMAS 5 OPERAÇÕES ===")
    print(df_historico[['Data', 'Tipo', 'Preço BTC (R$)', 'RSI', 'Sinal', 'BTC Total']].tail().to_string(index=False))
    
    # Análise de performance
    if operacoes_venda > 0:
        lucro_medio_por_operacao = (total_vendido - total_investido) / operacoes_venda
        print(f"\n=== ANÁLISE DE PERFORMANCE ===")
        print(f"Lucro médio por ciclo completo: R$ {lucro_medio_por_operacao:.2f}")
        print(f"Taxa de sucesso: {(operacoes_venda / operacoes_compra * 100):.1f}% (vendas/compras)")
        
        # Análise dos sinais
        sinais_compra = df_historico[df_historico['Tipo'] == 'COMPRA']['Sinal'].value_counts()
        sinais_venda = df_historico[df_historico['Tipo'] == 'VENDA']['Sinal'].value_counts()
        print(f"\nDistribuição dos sinais de compra:")
        for sinal, count in sinais_compra.items():
            print(f"  {sinal}: {count}")
        print(f"\nDistribuição dos sinais de venda:")
        for sinal, count in sinais_venda.items():
            print(f"  {sinal}: {count}")
    
    # Salvar histórico em CSV
    df_historico.to_csv('historico_ema_rsi_bitcoin.csv', index=False)
    print(f"\nHistórico salvo em: historico_ema_rsi_bitcoin.csv")
else:
    print("\nNenhuma operação foi realizada no período.")

# Comparação com estratégia Buy and Hold
valor_buy_hold = valor_operacao * (preco_final / df['Fechamento'].iloc[21])  # Começar do mesmo ponto
print(f"\n=== COMPARAÇÃO COM BUY AND HOLD ===")
print(f"Se tivesse comprado R$ {valor_operacao:.2f} no início e segurado: R$ {valor_buy_hold:.2f}")
print(f"Diferença da estratégia EMA+RSI: R$ {patrimonio_total - valor_buy_hold:.2f}")

# Gráfico da evolução (opcional - requer matplotlib)
try:
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(15, 16))
    
    # Gráfico 1: Preço do Bitcoin com EMAs e pontos de operação
    ax1.plot(df['Hora Abertura'], df['Fechamento'], label='Preço BTC (R$)', color='black', linewidth=1)
    ax1.plot(df['Hora Abertura'], df['EMA_9'], label='EMA 9', color='blue', alpha=0.7)
    ax1.plot(df['Hora Abertura'], df['EMA_21'], label='EMA 21', color='red', alpha=0.7)
    
    if historico_operacoes:
        compras = [op for op in historico_operacoes if op['Tipo'] == 'COMPRA']
        vendas = [op for op in historico_operacoes if op['Tipo'] == 'VENDA']
        
        if compras:
            ax1.scatter([op['Data'] for op in compras], [op['Preço BTC (R$)'] for op in compras], 
                       color='green', marker='^', s=100, label='Compras', zorder=5)
        if vendas:
            ax1.scatter([op['Data'] for op in vendas], [op['Preço BTC (R$)'] for op in vendas], 
                       color='red', marker='v', s=100, label='Vendas', zorder=5)
    
    ax1.set_title('Estratégia EMA 9/21 + RSI - Preço do Bitcoin com Sinais')
    ax1.set_ylabel('Preço (R$)')
    ax1.legend()
    ax1.grid(True)
    
    # Gráfico 2: RSI
    ax2.plot(df['Hora Abertura'], df['RSI'], label='RSI', color='purple')
    ax2.axhline(y=rsi_overbought, color='red', linestyle='--', alpha=0.7, label=f'Sobrecomprado ({rsi_overbought})')
    ax2.axhline(y=rsi_oversold, color='green', linestyle='--', alpha=0.7, label=f'Sobrevendido ({rsi_oversold})')
    ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='Linha Central (50)')
    ax2.set_title('Índice de Força Relativa (RSI)')
    ax2.set_ylabel('RSI')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True)
    
    # Gráfico 3: Evolução do patrimônio
    if historico_operacoes:
        patrimonio_acumulado = []
        for i, op in enumerate(historico_operacoes):
            if i == 0:
                if op['Tipo'] == 'COMPRA':
                    patrimonio_acumulado.append(-op['Valor Operação (R$)'])
                else:
                    patrimonio_acumulado.append(op['Valor Operação (R$)'])
            else:
                if op['Tipo'] == 'COMPRA':
                    patrimonio_acumulado.append(patrimonio_acumulado[-1] - op['Valor Operação (R$)'])
                else:
                    patrimonio_acumulado.append(patrimonio_acumulado[-1] + op['Valor Operação (R$)'])
        
        ax3.plot([op['Data'] for op in historico_operacoes], patrimonio_acumulado, 
                label='Patrimônio Acumulado', color='blue', marker='o', markersize=4)
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax3.set_title('Evolução do Patrimônio')
        ax3.set_ylabel('Valor (R$)')
        ax3.legend()
        ax3.grid(True)
    
    # Gráfico 4: Distribuição de operações por sinal
    if historico_operacoes:
        sinais = df_historico['Sinal'].value_counts()
        ax4.bar(range(len(sinais)), sinais.values, color=['green', 'red', 'blue', 'orange'][:len(sinais)])
        ax4.set_xticks(range(len(sinais)))
        ax4.set_xticklabels(sinais.index, rotation=45, ha='right')
        ax4.set_title('Distribuição de Operações por Sinal')
        ax4.set_ylabel('Quantidade')
        ax4.grid(True, axis='y')
    
    plt.tight_layout()
    plt.savefig('analise_ema_rsi_bitcoin.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Gráficos salvos em: analise_ema_rsi_bitcoin.png")
    
except ImportError:
    print("\nPara visualizar gráficos, instale matplotlib: pip install matplotlib")