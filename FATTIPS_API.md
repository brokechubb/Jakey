# API Documentation

## Base URL

- Development: `http://localhost:3001`
- Production: `https://codestats.gg/api`

## Authentication

All API endpoints require authentication via API key.

Include in header:

```
X-API-Key: your_api_key_here
```

## Endpoints

### Health Check

#### Get Health Status

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T12:00:00.000Z"
}
```

---

### Users

#### Get User

```http
GET /api/users/:discordId
```

Response:

```json
{
  "discordId": "123456789",
  "walletPubkey": "abc123...",
  "username": "username#1234",
  "createdAt": "2024-01-01T00:00:00.000Z",
  "lastActive": "2024-01-15T12:00:00.000Z",
  "_count": {
    "sentTips": 10,
    "receivedTips": 5,
    "airdropsCreated": 2,
    "participations": 8
  }
}
```

**Note:** Sensitive fields (encryptedPrivkey, encryptedMnemonic, keySalt, mnemonicSalt) are excluded from the response.

---

### Wallet

#### Create Wallet

```http
POST /api/wallet/create
Content-Type: application/json

{
  "discordId": "123456789"
}
```

Response:

```json
{
  "success": true,
  "discordId": "123456789",
  "walletPubkey": "7nYhPEv6s6DkXwJv7QxQwJ6Qz9H2LZv6rK5hLM8Jz3Tm",
  "privateKey": "4Z7v...,"
  "mnemonic": "apple banana cherry date..."
}
```

**⚠️ Security Note:** The private key and mnemonic are returned once. Store securely. Never expose in logs or client-side code.

#### Get Wallet Info

```http
GET /api/wallet/:discordId
```

Response:

```json
{
  "discordId": "123456789",
  "walletPubkey": "7nYhPEv6s6DkXwJv7QxQwJ6Qz9H2LZv6rK5hLM8Jz3Tm",
  "hasMnemonic": true,
  "createdAt": "2024-01-15T12:00:00.000Z"
}
```

#### Delete Wallet

```http
DELETE /api/wallet/:discordId
```

Response:

```json
{
  "success": true,
  "message": "Wallet deleted",
  "discordId": "123456789"
}
```

---

### Balance

#### Get User Balance

```http
GET /api/balance/:discordId
```

Response:

```json
{
  "discordId": "123456789",
  "walletPubkey": "abc123...",
  "balances": {
    "sol": 1.5,
    "usdc": 100.0,
    "usdt": 50.0
  }
}
```

---

### Send & Tips

#### Send Tip (Single Recipient)

```http
POST /api/send/tip
Content-Type: application/json

{
  "fromDiscordId": "123456789",
  "toDiscordId": "987654321",
  "amount": 5.0,
  "token": "SOL",
  "amountType": "token" // or "usd"
}
```

Response:

```json
{
  "success": true,
  "signature": "5abc123...",
  "from": "123456789",
  "to": "987654321",
  "amountToken": 5.0,
  "amountUsd": 750.0,
  "token": "SOL",
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

#### Send Batch Tip (Multiple Recipients)

```http
POST /api/send/batch-tip
Content-Type: application/json

{
  "fromDiscordId": "123456789",
  "recipients": [
    { "discordId": "987654321" },
    { "discordId": "111222333" },
    { "discordId": "444555666" }
  ],
  "totalAmount": 15.0,
  "token": "SOL",
  "amountType": "token"
}
```

Response:

```json
{
  "success": true,
  "signature": "5abc123...",
  "from": "123456789",
  "recipients": [
    { "to": "987654321", "signature": "5abc123...:0", "amountToken": 5, "amountUsd": 750 },
    { "to": "111222333", "signature": "5abc123...:1", "amountToken": 5, "amountUsd": 750 },
    { "to": "444555666", "signature": "5abc123...:2", "amountToken": 5, "amountUsd": 750 }
  ],
  "totalAmountToken": 15,
  "totalAmountUsd": 2250,
  "token": "SOL",
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

#### Withdraw Funds

```http
POST /api/send/withdraw
Content-Type: application/json

{
  "discordId": "123456789",
  "destinationAddress": "ExternalWalletAddress...",
  "amount": 1.0,
  "token": "SOL"
}

// Use amount: null or omit for max withdrawal
```

Response:

```json
{
  "success": true,
  "signature": "5abc123...",
  "from": "abc123...",
  "to": "ExternalWalletAddress...",
  "amountToken": 1.0,
  "amountUsd": 150.0,
  "token": "SOL",
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

---

### Transactions

#### Get Transaction by ID or Signature

```http
GET /api/transactions/:id
```

Query params:

- `:id`: Transaction UUID or Solana signature

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "signature": "5abc123...",
  "txType": "TIP",
  "status": "CONFIRMED",
  "amount": 5.0,
  "amountUsd": 750.0,
  "token": "SOL",
  "fromId": "123456789",
  "toId": "987654321",
  "createdAt": "2024-01-15T12:00:00.000Z"
}
```

#### Get User Transactions

```http
GET /api/transactions/user/:discordId
```

Query params:

- `limit`: Number of results (default: 10, max: 50)
- `offset`: Pagination offset (default: 0)

Response:

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "signature": "5abc123...",
    "txType": "TIP",
    "status": "CONFIRMED",
    "amount": 5.0,
    "amountUsd": 750.0,
    "token": "SOL",
    "fromId": "123456789",
    "toId": "987654321",
    "createdAt": "2024-01-15T12:00:00.000Z"
  }
]
```

---

### Airdrops

#### Create Airdrop

```http
POST /api/airdrops/create
Content-Type: application/json

{
  "creatorDiscordId": "123456789",
  "amount": 10.0,
  "token": "SOL",
  "duration": "10m",
  "maxWinners": 5,
  "amountType": "token" // or "usd"
}
```

Response:

```json
{
  "success": true,
  "airdropId": "uuid-uuid-uuid",
  "potSize": 10.0,
  "token": "SOL",
  "totalUsd": 1500.0,
  "expiresAt": "2024-01-15T12:10:00.000Z",
  "maxWinners": 5,
  "ephemeralWallet": "ephemeral123..."
}
```

#### Get Airdrop Details

```http
GET /api/airdrops/:id
```

Response:

```json
{
  "id": "uuid-uuid-uuid",
  "creatorId": "123456789",
  "potSize": 10.0,
  "tokenMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "participantCount": 3,
  "maxParticipants": 5,
  "status": "ACTIVE",
  "expiresAt": "2024-01-15T12:10:00.000Z",
  "createdAt": "2024-01-15T12:00:00.000Z",
  "participants": [{ "discordId": "987654321", "status": "TRANSFERRED", "shareAmount": 3.33 }]
}
```

#### Claim Airdrop

```http
POST /api/airdrops/:id/claim
Content-Type: application/json

{
  "discordId": "987654321"
}
```

Response:

```json
{
  "success": true,
  "airdropId": "uuid-uuid-uuid",
  "claimant": "987654321",
  "amountReceived": 3.33,
  "tokenMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "signature": "5abc123...",
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

#### List Airdrops

```http
GET /api/airdrops?status=ACTIVE&limit=10&offset=0
```

Query params:

- `status`: ACTIVE, EXPIRED, SETTLED, RECLAIMED
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)

Response:

```json
{
  "airdrops": [
    {
      "id": "uuid-uuid-uuid",
      "creatorId": "123456789",
      "potSize": 10.0,
      "tokenMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "participantCount": 3,
      "maxParticipants": 5,
      "status": "ACTIVE",
      "expiresAt": "2024-01-15T12:10:00.000Z"
    }
  ],
  "total": 1
}
```

---

### Rain

#### Create Rain

```http
POST /api/rain/create
Content-Type: application/json

{
  "creatorDiscordId": "123456789",
  "amount": 5.0,
  "token": "SOL",
  "winners": ["987654321", "111222333", "444555666"],
  "amountType": "token"
}
```

Response:

```json
{
  "success": true,
  "signature": "5abc123...",
  "creator": "123456789",
  "winners": [
    {
      "discordId": "987654321",
      "signature": "5abc123...:0",
      "amountToken": 1.66,
      "amountUsd": 249
    },
    {
      "discordId": "111222333",
      "signature": "5abc123...:1",
      "amountToken": 1.66,
      "amountUsd": 249
    },
    { "discordId": "444555666", "signature": "5abc123...:2", "amountToken": 1.66, "amountUsd": 249 }
  ],
  "totalAmountToken": 5.0,
  "totalAmountUsd": 750,
  "token": "SOL",
  "amountPerUser": 1.66,
  "winnersCount": 3,
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

**Jakey Trivia Example:**

```javascript
// Jakey rains on trivia winners
const response = await fetch('https://codestats.gg/api/rain/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.FATTIPS_API_KEY,
  },
  body: JSON.stringify({
    creatorDiscordId: process.env.JAKEY_DISCORD_ID,
    amount: 10,
    token: 'SOL',
    winners: ['winner1', 'winner2', 'winner3'],
    amountType: 'token',
  }),
});

const result = await response.json();
console.log(`Rained ${result.amountPerUser} SOL on ${result.winnersCount} winners!`);
```

---

### Token Swaps

#### Get Swap Quote

```http
GET /api/swap/quote?inputToken=SOL&outputToken=USDC&amount=1.0&amountType=token
```

Response:

```json
{
  "inputToken": "SOL",
  "outputToken": "USDC",
  "inputAmount": 1.0,
  "outputAmount": 95.50,
  "priceImpact": 0.05,
  "routePlan": [...],
  "inputUsd": 150.00,
  "outputUsd": 95.50
}
```

#### Execute Swap

```http
POST /api/swap/execute
Content-Type: application/json

{
  "discordId": "123456789",
  "inputToken": "SOL",
  "outputToken": "USDC",
  "amount": 1.0,
  "amountType": "token",
  "slippage": 1.0 // optional, default 1%
}
```

Response:

```json
{
  "success": true,
  "signature": "5abc123...",
  "inputToken": "SOL",
  "outputToken": "USDC",
  "inputAmount": 1.0,
  "outputAmount": 95.42,
  "inputUsd": 150.0,
  "outputUsd": 95.42,
  "priceImpact": 0.08,
  "solscanUrl": "https://solscan.io/tx/5abc123..."
}
```

#### Get Supported Tokens

```http
GET /api/swap/supported-tokens
```

Response:

```json
{
  "tokens": [
    { "symbol": "SOL", "mint": "So11111111111111111111111111111111111111112", "decimals": 9 },
    { "symbol": "USDC", "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "decimals": 6 },
    { "symbol": "USDT", "mint": "Es9vMFrzaCERmBfrE5j5K3x4DCD9Xyj1eN3y1X5j1vT8", "decimals": 6 }
  ]
}
```

---

### Leaderboard

#### Get Top Tippers

```http
GET /api/leaderboard/top-tippers?limit=10
```

Response:

```json
[
  {
    "discordId": "123456789",
    "wallet": "abc123...",
    "totalTippedUsd": 5000.0
  }
]
```

#### Get Top Receivers

```http
GET /api/leaderboard/top-receivers?limit=10
```

Response:

```json
[
  {
    "discordId": "123456789",
    "wallet": "abc123...",
    "totalReceivedUsd": 3500.0
  }
]
```

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Error message describing the issue"
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized"
}
```

### 404 Not Found

```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error"
}
```

---

## Rate Limits

- 100 requests per minute per IP
- 1000 requests per minute per authenticated user

---

## Jakey Integration Examples

### Jakey Tips a User

```javascript
// Jakey tipping user123
const response = await fetch('https://codestats.gg/api/send/tip', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.FATTIPS_API_KEY,
  },
  body: JSON.stringify({
    fromDiscordId: process.env.JAKEY_DISCORD_ID,
    toDiscordId: 'user123',
    amount: 5,
    token: 'SOL',
    amountType: 'token',
  }),
});

const result = await response.json();
if (result.success) {
  console.log(`Tipped! Transaction: ${result.solscanUrl}`);
}
```

### Jakey Creates an Airdrop

```javascript
// Jakey creating a community airdrop
const response = await fetch('https://codestats.gg/api/airdrops/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.FATTIPS_API_KEY,
  },
  body: JSON.stringify({
    creatorDiscordId: process.env.JAKEY_DISCORD_ID,
    amount: 100,
    token: 'USDC',
    duration: '1h',
    maxWinners: 10,
    amountType: 'usd',
  }),
});

const result = await response.json();
console.log(`Airdrop created! ID: ${result.airdropId}`);
```

### Jakey Checks User Balance

```javascript
// Jakey checking if user can afford something
const response = await fetch('https://codestats.gg/api/balance/user123', {
  headers: {
    'X-API-Key': process.env.FATTIPS_API_KEY,
  },
});

const { balances } = await response.json();
if (balances.sol >= 1) {
  // User has at least 1 SOL
}
```

### Jakey Executes a Swap

```javascript
// Jakey swapping SOL for USDC for a user
const quote = await fetch(
  'https://codestats.gg/api/swap/quote?inputToken=SOL&outputToken=USDC&amount=2&amountType=token',
  {
    headers: { 'X-API-Key': process.env.FATTIPS_API_KEY },
  }
);

const swap = await fetch('https://codestats.gg/api/swap/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.FATTIPS_API_KEY,
  },
  body: JSON.stringify({
    discordId: 'user123',
    inputToken: 'SOL',
    outputToken: 'USDC',
    amount: 2,
    amountType: 'token',
  }),
});
```
