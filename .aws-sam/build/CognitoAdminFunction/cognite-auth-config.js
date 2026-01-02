// 開発環境専用設定
const COGNITE_AUTH_CONFIG = {
    CLIENT_ID: 'dev-client-id',
    TENANT_DOMAIN: 'dev-tenant.auth.region.amazoncognito.com',
    REDIRECT_URI: `${window.location.origin}/callback.html`,
    SCOPE: 'openid profile email',
    RESPONSE_TYPE: 'id_token'
};

// 設定取得関数
function getCogniteConfig() {
    return COGNITE_AUTH_CONFIG;
}

// 開発環境判定（常にtrue）
function isDevelopmentMode() {
    return true;
}