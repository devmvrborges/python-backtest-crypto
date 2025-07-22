from binance.client import Client
import datetime, pandas as pd
import numpy as np

client = Client()
start = datetime.datetime(2025, 3, 31)
end = datetime.datetime(2025, 6, 30)

klines = client.get_historical_klines(
    'BTCBRL',  # Bitcoin em Reais
    Client.KLINE_INTERVAL_1HOUR,  # Intervalos de 6 horas
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

# Estratégia de Dollar Cost Averaging (DCA)
investimento_por_compra = 3.00  # R$ 3,00 a cada 1 horas
total_investido = 0
bitcoin_acumulado = 0
historico_compras = []

print("=== SIMULAÇÃO DE INVESTIMENTO EM BITCOIN ===")
print(f"Investimento: R$ {investimento_por_compra:.2f} a cada 1 hora")
print(f"Período: {start.strftime('%d/%m/%Y')} até {end.strftime('%d/%m/%Y')}")
print("\n" + "="*60)

# Simular compras a cada 1 horas
for index, row in df.iterrows():
    preco_bitcoin = row['Fechamento']
    data_compra = row['Hora Abertura']
    
    # Calcular quantos satoshis/bitcoin compramos com R$ 3,00
    bitcoin_comprado = investimento_por_compra / preco_bitcoin
    
    # Atualizar totais
    total_investido += investimento_por_compra
    bitcoin_acumulado += bitcoin_comprado
    
    # Registrar compra
    historico_compras.append({
        'Data': data_compra,
        'Preço BTC (R$)': preco_bitcoin,
        'Investimento (R$)': investimento_por_compra,
        'BTC Comprado': bitcoin_comprado,
        'BTC Total': bitcoin_acumulado,
        'Total Investido (R$)': total_investido
    })

# Calcular resultado final
preco_final = df['Fechamento'].iloc[-1]
valor_atual_carteira = bitcoin_acumulado * preco_final
lucro_prejuizo = valor_atual_carteira - total_investido
rentabilidade_percentual = (lucro_prejuizo / total_investido) * 100

# Exibir resultados
print(f"\n=== RESULTADOS FINAIS ===")
print(f"Total de compras realizadas: {len(df)}")
print(f"Total investido: R$ {total_investido:.2f}")
print(f"Bitcoin acumulado: {bitcoin_acumulado:.8f} BTC")
print(f"Preço final do Bitcoin: R$ {preco_final:.2f}")
print(f"Valor atual da carteira: R$ {valor_atual_carteira:.2f}")
print(f"Lucro/Prejuízo: R$ {lucro_prejuizo:.2f}")
print(f"Rentabilidade: {rentabilidade_percentual:.2f}%")

# Criar DataFrame com histórico de compras
df_historico = pd.DataFrame(historico_compras)

# Mostrar primeiras e últimas 5 compras
print(f"\n=== PRIMEIRAS 5 COMPRAS ===")
print(df_historico.head().to_string(index=False))

print(f"\n=== ÚLTIMAS 5 COMPRAS ===")
print(df_historico.tail().to_string(index=False))

# Análise adicional
preco_medio_compra = total_investido / bitcoin_acumulado
print(f"\n=== ANÁLISE ADICIONAL ===")
print(f"Preço médio de compra: R$ {preco_medio_compra:.2f}")
print(f"Diferença do preço atual: {((preco_final - preco_medio_compra) / preco_medio_compra * 100):.2f}%")

# Salvar histórico em CSV (opcional)
df_historico.to_csv('historico_investimento_bitcoin.csv', index=False)
print(f"\nHistórico salvo em: historico_investimento_bitcoin.csv")

# Gráfico simples da evolução (opcional - requer matplotlib)
try:
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Gráfico 1: Preço do Bitcoin ao longo do tempo
    ax1.plot(df['Hora Abertura'], df['Fechamento'], label='Preço BTC (R$)', color='orange')
    ax1.set_title('Evolução do Preço do Bitcoin')
    ax1.set_ylabel('Preço (R$)')
    ax1.legend()
    ax1.grid(True)
    
    # Gráfico 2: Valor da carteira vs Total investido
    df_historico['Valor Carteira'] = df_historico['BTC Total'] * df['Fechamento'].values
    ax2.plot(df_historico['Data'], df_historico['Total Investido (R$)'], label='Total Investido', color='blue')
    ax2.plot(df_historico['Data'], df_historico['Valor Carteira'], label='Valor da Carteira', color='green')
    ax2.set_title('Investimento vs Valor da Carteira')
    ax2.set_ylabel('Valor (R$)')
    ax2.set_xlabel('Data')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('analise_investimento_bitcoin.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Gráficos salvos em: analise_investimento_bitcoin.png")
    
except ImportError:
    print("\nPara visualizar gráficos, instale matplotlib: pip install matplotlib")